include_directories("/usr/local/include/");
#include <opencv4/opencv2/opencv.hpp>

int main(int argh, char* argv[])
{
    cv::VideoCapture cap(0);

    if(!cap.isOpened())
    {
        return -1;
    }

    cv::Mat frame; 
    while(cap.read(frame))
    {
        //
        //取得したフレーム画像に対して，クレースケール変換や2値化などの処理を書き込む．
        //

        cv::imshow("win", frame);
        const int key = cv::waitKey(1);
        if(key == 'q'/*113*/)
        {
            break;
        }
    }
    cv::destroyAllWindows();
    return 0;
}
