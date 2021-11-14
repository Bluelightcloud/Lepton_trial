#include <stdio.h>
#include <cstring>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>

int main(){
	char buf[4096] = "376,336,123,73,387,279,97,81,";
	signed int point[8] = {0};
	int j = 0;
	int digit = 0;

	for (int i = 0; i <= 7; i++){
	    while(1){
	        if(buf[j] == ','){
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
	}
}