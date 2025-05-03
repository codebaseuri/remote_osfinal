
unsigned char port_byte_in(unsigned short port)
{
    unsigned char result;
    __asm__("in %%dx, %%al" : "=a" (result) : "d" (port));
    return result;
}
void port_byte_out(unsigned short port,unsigned char data)
{
    __asm__("out %%al, %%dx" : : "a" (data), "d" (port));
}
void memory_copy(char *start,char *dest, int amount)
{
    for (int i=0;i<amount;i++)
    {
        dest[i]=start[i];
    }
}
int string_compare(char *str1,char *str2)
{
    int i=0;
    for (int k = 0; str1[k] != '\0' && str2[k] != '\0'; k++)
    {
       
        if (str1[k] != str2[k])
        {
            return 0;
        }
        
        i=k;
    }
    if (str1[i+1] == '\0' && str2[i+1] == '\0')

    {
        return 1;
    }
    return 0;
}
void delay(int count) {
    // Nested loop for better delay control
    volatile int outer, inner;
    for (outer = 0; outer < count; outer++) {
        for (inner = 0; inner < 3000000; inner++) {

            __asm__("nop");
        }
    }
}