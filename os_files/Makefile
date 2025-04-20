# Makefile for OS development in WSL with separate terminal for QEMU
# Define source directory
SRC_DIR = .

# First rule is the one executed when no parameters are fed to the Makefile
all: run

# List of all C source files
C_SOURCES := $(wildcard $(SRC_DIR)/*.c)
# Corresponding object files for the C sources
C_OBJECTS := $(C_SOURCES:.c=.o)

# Rule to link all object files into a binary
dummy_kernel.bin: $(SRC_DIR)/enter_kernel.o $(C_OBJECTS) $(SRC_DIR)/internal_isrs.o
	# Link the object files and create a binary
	ld -m elf_i386 -o $@ -Ttext 0x1000 $^ --oformat binary

# Assembly file compilation (for .asm files)
%.o: %.asm
	# Assemble the assembly files into object files
	nasm -f elf32 $< -o $@

# General rule for compiling .c files into .o files
%.o: %.c
	# Compile the .c files with necessary flags for kernel code
	gcc -m32 -ffreestanding -fno-pie -c $< -o $@

# Rule for assembling the bootloader
bootable.bin: $(SRC_DIR)/bootable.asm
	# Assemble the bootloader code into a binary
	nasm $< -f bin -o $@

# Rule to create the final OS image
os-image.bin: bootable.bin dummy_kernel.bin
	# Combine bootloader and kernel binary into one OS image
	cat $^ > $@

# Run the OS image using QEMU in a new Windows Terminal window
run: os-image.bin
	powershell.exe -Command "wt -w 0 wsl.exe -d Ubuntu qemu-system-i386 -fda $(PWD)/os-image.bin -display curses"

# Run in SDL mode (requires X server setup)
run-sdl: os-image.bin
	powershell.exe -Command "wt -w 0 wsl.exe -d Ubuntu qemu-system-i386 -fda $(PWD)/os-image.bin -display sdl"

# Run with VNC
run-vnc: os-image.bin
	powershell.exe -Command "wt -w 0 wsl.exe -d Ubuntu qemu-system-i386 -fda $(PWD)/os-image.bin -display vnc=:0"

# Clean up object files and binaries
clean:
	rm -f *.bin *.o *.dis $(SRC_DIR)/*.o
