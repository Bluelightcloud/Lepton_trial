#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>                /* low-level i/o */
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <malloc.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/ioctl.h>
#include <linux/videodev2.h>
#include <pthread.h>
#include <semaphore.h>
#include <iostream>
#include <fstream>
#include <ctime>
#include <stdint.h>
#include <termios.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <cstring>
#include <math.h>

#include "Palettes.h"
#include "SPI.h"
#include "Lepton_I2C.h"

#define PACKET_SIZE 164
#define PACKET_SIZE_UINT16 (PACKET_SIZE/2)
#define PACKETS_PER_FRAME 60
#define FRAME_SIZE_UINT16 (PACKET_SIZE_UINT16*PACKETS_PER_FRAME)
#define FPS 27;

using std::endl;
using std::ofstream;
ofstream ofs("data.csv");
time_t startt = time(NULL);

static char buf[4096];
static signed int point[8] = {0};

static char const *v4l2dev = "/dev/video1";
static char *spidev = NULL;
static int v4l2sink = -1;
static int width = 80;                //640;    // Default for Flash
static int height = 60;        //480;    // Default for Flash
static char *vidsendbuf = NULL;
static int vidsendsiz = 0;

static int resets = 0;
static uint8_t result[PACKET_SIZE*PACKETS_PER_FRAME];
static uint16_t *frameBuffer;

/*
static int kbhit(){
    struct termios oldt, newt;
    int ch;
    int oldf;

    tcgetattr(STDIN_FILENO, &oldt);
    newt = oldt;
    newt.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &newt);
    oldf = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, oldf | O_NONBLOCK);

    ch = getchar();

    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
    fcntl(STDIN_FILENO, F_SETFL, oldf);

    if (ch != EOF)
    {
        ungetc(ch, stdin);
        return 1;
    }

    return 0;
}
*/

static void write_csv(uint16_t dist[]){
    time_t t = time(NULL);
    ofs << t-startt << ',';
    for (int i = 0; i < 61; i++) {
        ofs << dist[i] << ',';
    }
    ofs << endl;
}

static void init_device() {
    SpiOpenPort(spidev);
}

static void grab_frame() {
    resets = 0;
    for (int j = 0; j < PACKETS_PER_FRAME; j++) {
        read(spi_cs_fd, result + sizeof(uint8_t) * PACKET_SIZE * j, sizeof(uint8_t) * PACKET_SIZE);
        int packetNumber = result[j * PACKET_SIZE + 1];
        if (packetNumber != j) {
            j = -1;
            resets += 1;
            usleep(1000);
            if (resets == 750) {
                SpiClosePort();
                usleep(750000);
                SpiOpenPort(spidev);
            }
        }
    }
    if (resets >= 30) {
        fprintf( stderr, "done reading, resets: \n" );
    }

    frameBuffer = (uint16_t *)result;
    int row, column;
    uint16_t value;
    uint16_t minValue = 65535;
    uint16_t maxValue = 0;
    uint16_t minTh = 29000;
    uint16_t maxTh = 31315;
    uint16_t dist[61] = {};
    int counter = 0;
    int mouth = point[0] + (80*point[1]);
    int mouthp = mouth + point[2];
    int mouthl = point[3];
    int mouthc = 1;
    int nose = point[4] + (80*point[5]);
    int nosep = nose + point[6];
    int nosel = point[7];
    int nosec = 1;
    
    
    for (int i = 0; i < FRAME_SIZE_UINT16; i++) {
        if (i % PACKET_SIZE_UINT16 < 2) {
            continue;
        }
        
        int temp = result[i * 2];
        result[i * 2] = result[i * 2 + 1];
        result[i * 2 + 1] = temp;
        counter++;
        
        if((counter > nosep)&&(nosec < nosel)){
            nose += 80;
            nosep += 80;
            nosec++;
        }else if(nosec == nosel){
            nose = -1;
        }
        
        if((counter > mouthp)&&(mouthc < mouthl)){
            mouth += 80;
            mouthp += 80;
            mouthc++;
        }else if(mouthc == mouthl){
            mouth = -1;
        }
        
        if((((counter < mouth)||(mouth < 0))&&((counter < nose)||(nose < 0)))||((nose < 0)&&(mouth < 0))){
            frameBuffer[i] = 27315;
        }
        value = frameBuffer[i];
        
/*---------------------------------fill ver
        if((counter > nosep)&&(nosec < nosel)){
            nose += 80;
            nosep += 80;
            nosec++;
        }
        if((counter >= nose)&&(counter <= nosep)){
            frameBuffer[i] = 30000;
        }
        
        if((counter > mouthp)&&(mouthc < mouthl)){
            mouth += 80;
            mouthp += 80;
            mouthc++;
        }
        if((counter >= mouth)&&(counter <= mouthp)){
            frameBuffer[i] = 30000;
        }

/*---------------------------------mode calc
        if(value >= minTh){
            for(int j = 0; j < 60; j++){
                if(value < minTh + (10*(j+1))){
                    dist[j] += 1;
                    break;
                }
                if(j == 60){
                    dist[60] += 1;
                    break;
                }
            }
        }
---------------------------------*/
        if (value > maxValue) {
            maxValue = value;
        }
        if (value < minValue) {
            minValue = value;
        }
        column = i % PACKET_SIZE_UINT16 - 2;
        row = i / PACKET_SIZE_UINT16;
    } 
    //write_csv(dist);
    float diff = maxValue - minTh;
    float scale = 255 / diff;
    for (int i = 0; i < FRAME_SIZE_UINT16; i++) {
        if (i % PACKET_SIZE_UINT16 < 2) {
            continue;
        }
        value = (frameBuffer[i] - minValue) * scale;
        const int *colormap = colormap_ironblack;
        column = (i % PACKET_SIZE_UINT16) - 2;
        row = i / PACKET_SIZE_UINT16;

        // Set video buffer pixel to scaled colormap value
        int idx = row * width * 3 + column * 3;
        vidsendbuf[idx + 0] = colormap[3 * value];
        vidsendbuf[idx + 1] = colormap[3 * value + 1];
        vidsendbuf[idx + 2] = colormap[3 * value + 2];
    }

    /*
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    memset( vidsendbuf, 0, 3);
    memcpy( vidsendbuf+3, vidsendbuf, vidsendsiz-3 );
    */
}

static void stop_device() {
    SpiClosePort();
}

static void open_vpipe()
{
    v4l2sink = open(v4l2dev, O_WRONLY);
    if (v4l2sink < 0) {
        fprintf(stderr, "Failed to open v4l2sink device. (%s)\n", strerror(errno));
        exit(-2);
    }
    // setup video for proper format
    struct v4l2_format v;
    int t;
    v.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    t = ioctl(v4l2sink, VIDIOC_G_FMT, &v);
    if( t < 0 )
        exit(t);
    v.fmt.pix.width = width;
    v.fmt.pix.height = height;
    v.fmt.pix.pixelformat = V4L2_PIX_FMT_RGB24;
    vidsendsiz = width * height * 3;
    v.fmt.pix.sizeimage = vidsendsiz;
    t = ioctl(v4l2sink, VIDIOC_S_FMT, &v);
    if( t < 0 )
        exit(t);
    vidsendbuf = (char*)malloc( vidsendsiz );
}

static pthread_t sender;
static pthread_t udp;
static sem_t lock1,lock2;
static void *sendvid(void *v)
{
    (void)v;
    for (;;) {
        sem_wait(&lock1);
        if (vidsendsiz != write(v4l2sink, vidsendbuf, vidsendsiz))
            exit(-1);
        sem_post(&lock2);
    }
}

static void *grab_UDP(void *v){
    (void)v;
    int sock;
    struct sockaddr_in addr;

    sock = socket(AF_INET, SOCK_DGRAM, 0);

    addr.sin_family = AF_INET;
    addr.sin_port = htons(11111);
    addr.sin_addr.s_addr = INADDR_ANY;

    bind(sock, (struct sockaddr *)&addr, sizeof(addr));
    int rsize;
    while( 1 ) {
      memset(buf, 0, sizeof(buf));
      rsize = recv(sock, buf, sizeof(buf), 0);

      if ( rsize == 0 ) {
          break;
      } else if ( rsize == -1 ) {
          perror( "recv" );
      } else {
          //printf( "receive:%s\n", buf );
          int j = 0;
          int digit = 0;
          for (int i = 0; i <= 7; i++){
              while(1){
                  if(buf[j] == ','){
                      point[i] = 0;
                      for(int l = digit; l != 0; --l){
                          point[i] += ((int)buf[j-l]-48)*pow(10, l-1);
                      }
                      j++;
                      digit = 0;
                      break;
                  }
                  j++;
                  digit++;
              }
          }


          for(int k = 0; k <= 7; k++){
              printf("%d,",point[k]);
              if(k == 7){
                    printf("\n");
              }
          }
      }
    }

    close(sock);
}

void usage(char *exec)
{
    printf("Usage: %s [options]\n"
           "Options:\n"
           "  -d | --device name       Use name as spidev device "
               "(/dev/spidev0.1 by default)\n"
           "  -h | --help              Print this message\n"
           "  -v | --video name        Use name as v4l2loopback device "
               "(%s by default)\n"
           "", exec, v4l2dev);
}

static const char short_options [] = "d:hv:";

static const struct option long_options [] = {
    { "device",  required_argument, NULL, 'd' },
    { "help",    no_argument,       NULL, 'h' },
    { "video",   required_argument, NULL, 'v' },
    { 0, 0, 0, 0 }
};

int main(int argc, char **argv)
{
    struct timespec ts;

    // processing command line parameters
    for (;;) {
        int index;
        int c;

        c = getopt_long(argc, argv,
                        short_options, long_options,
                        &index);

        if (-1 == c)
            break;

        switch (c) {
            case 0:
                break;

            case 'd':
                spidev = optarg;
                break;

            case 'h':
                usage(argv[0]);
                exit(EXIT_SUCCESS);

            case 'v':
                v4l2dev = optarg;
                break;

            default:
                usage(argv[0]);
                exit(EXIT_FAILURE);
        }
    }

    open_vpipe();

    // open and lock response
    if (sem_init(&lock2, 0, 1) == -1)
        exit(-1);
    sem_wait(&lock2);

    if (sem_init(&lock1, 0, 1) == -1)
        exit(-1);
    pthread_create(&sender, NULL, sendvid, NULL);
//--------------------------------------
    pthread_create(&udp, NULL, grab_UDP, NULL);
//--------------------------------------
    

    for (;;) {
        // wait until a frame can be written
        fprintf( stderr, "Waiting for sink\n" );
        sem_wait(&lock2);
        // setup source
        init_device(); // open and setup SPI
        for (;;) {
            grab_frame();
            // push it out
            sem_post(&lock1);
            clock_gettime(CLOCK_REALTIME, &ts);
            ts.tv_sec += 2;
            // wait for it to get written (or is blocking)
            if (sem_timedwait(&lock2, &ts))
                break;
        }
        stop_device(); // close SPI
    }
    close(v4l2sink);
    return 0;
}
