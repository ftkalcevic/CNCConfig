#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main()
{
    system( "/sbin/poweroff" );
    return 0;
}
