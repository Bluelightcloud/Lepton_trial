#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <cstring>
#include <string.h>
#include <unistd.h>


int main()
{
   int sock;
   struct sockaddr_in addr;

   char buf[4096];

   sock = socket(AF_INET, SOCK_DGRAM, 0);

   addr.sin_family = AF_INET;
   addr.sin_port = htons(11111);
   addr.sin_addr.s_addr = INADDR_ANY;

   bind(sock, (struct sockaddr *)&addr, sizeof(addr));

   memset(buf, 0, sizeof(buf));
   int rsize;
   while( 1 ) {
      rsize = recv(sock, buf, sizeof(buf), 0);

      if ( rsize == 0 ) {
          break;
      } else if ( rsize == -1 ) {
          perror( "recv" );
      } else {
          printf( "receive:%s\n", buf );
      }
   }

   close(sock);

   return 0;
}
