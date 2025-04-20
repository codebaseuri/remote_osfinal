[BITS 16]
[ORG 0x7c00]


KERNEL_OFFSET equ 0x1000
;setup stack 
mov bp , 0x9000
mov sp,bp
mov [bootdrive],dl



mov si, Message
call print


call load_kernel
call switch_TO_32
jmp $

%include "disk.asm"
%include "gdt_setup.asm"
%include "to_protected.asm"



print:
    mov ah, 0x0e

    lopp:
    lodsb 
    cmp al,0
    jz return
    int 0x10

    jmp lopp
    return:
    ret

[BITS 16]
load_kernel:
    mov bx, KERNEL_OFFSET
    mov dh,50
    mov dl , [bootdrive]
    call disk_load
    ret

[BITS 32]
BEGIN_32BIT:
call KERNEL_OFFSET
jmp $


bootdrive db 0
Message db "I AM AM WELCOME TO MY WORLD!\n", 0
TIMES 510-($-$$) db 0
dw 0xaa55