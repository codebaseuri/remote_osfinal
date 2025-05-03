unsigned char port_byte_in(unsigned short port);
void port_byte_out(unsigned short port,unsigned char data);
void memory_copy(char *start,char *dest, int amount);
int string_compare(char *str1,char *str2);
void delay(int count);