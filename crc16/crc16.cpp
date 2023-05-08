/*
 * Copyright (c) 2014 Jonas Eriksson
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <stddef.h>
#include <sys/stat.h>
#include <fcntl.h>

/*
  Name  : CRC-16 CCITT
  Poly  : 0x1021    x^16 + x^12 + x^5 + 1
  Init  : 0
  Revert: false
  XorOut: 0x0000
  Check : 0x29B1 ("123456789")
  MaxLen: 4095 байт (32767 бит) - обнаружение
	одинарных, двойных, тройных и всех нечетных ошибок
*/
unsigned short Crc16(char* pcBlock, unsigned short len)
{
	unsigned short crc = 0;
	char i;

	while (len--)
	{
		crc ^= *pcBlock++ << 8;

		for (i = 0; i < 8; i++)
			crc = crc & 0x8000 ? (crc << 1) ^ 0x1021 : crc << 1;
	}
	return crc;
}
int main(int argc, char* argv[]) {
	char *buffer;
	long size;
	//читаем файл
	if(strcmp(argv[1],"file")==0){
		FILE* file = fopen(argv[2], "rb");

		//узнаем размер файла
		fseek(file, 0L, SEEK_END);
		size = ftell(file);
		fseek(file, 0, SEEK_SET);
		//читаем  
		buffer = (char*)malloc((size_t)size);
		fread((buffer), size, 1, file);
		fclose(file);
	}
	//берем строку из args
	else if(strcmp(argv[1],"string")==0){
		size = strlen(argv[2]);
		buffer = (char*)malloc((size_t)size);
		strcpy(buffer,argv[2]);
	}
	//printf("%d\n",size);
	//printf("%s\n",buffer);

	//считаем crc		
	uint16_t crc;
	crc = Crc16((buffer), (unsigned short)size);
	printf("0x%04hX\n", crc);
	free(buffer);
	return 0;
}
