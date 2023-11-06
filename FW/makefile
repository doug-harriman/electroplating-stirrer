# Seeded from: https://gist.github.com/edwardhotchkiss/9378977

DEVICE     = attiny85

# 1 MHz internal clock (default)
F_CPU      = 1000000

PROGRAMMER = usbtiny

COMPILER   = avr-gcc

CFLAGS =
CFLAGS += -DF_CPU=$(F_CPU)
CFLAGS += -mmcu=$(DEVICE)
CFLAGS += -DDEVICE=\"${DEVICE}\"
CFLAGS += -g
CFLAGS += -Os
CFLAGS += -Wall
CFLAGS += -Werror

SOURCES = $(wildcard *.c)
OBJECTS = $(SOURCES:.c=.o)

FILENAME_APP = main
FILENAME_SIM = sim

all: $(FILENAME_APP) $(FILENAME_SIM) flash sim

$(FILENAME_APP): $(OBJECTS)
	$(COMPILER)  $(CFLAGS) -o $(FILENAME_APP).elf $(filter-out main-sim.o, $(OBJECTS))
	avr-objcopy -j .text -j .data -O ihex $(FILENAME_APP).elf $(FILENAME_APP).hex
	avr-size --format=avr --mcu=$(DEVICE) $(FILENAME_APP).elf

$(FILENAME_SIM).elf: $(OBJECTS)
	$(COMPILER)  $(CFLAGS) -o $(FILENAME_SIM).elf $(filter-out main.o, $(OBJECTS))
	avr-objcopy -j .text -j .data -O ihex $(FILENAME_SIM).elf  $(FILENAME_SIM).hex
	avr-size --format=avr --mcu=$(DEVICE) $(FILENAME_SIM).elf

%.o: %.c
	$(COMPILER) $(CFLAGS) -c $< -o $@

flash: $(FILENAME_APP)
	sudo avrdude -p $(DEVICE) -c $(PROGRAMMER) -U flash:w:$(FILENAME_APP).hex:i

sim: $(FILENAME_SIM).elf
	simavr -m $(DEVICE) $(FILENAME_SIM).elf

sim-debug: $(FILENAME_SIM).elf
	simavr -g -m $(DEVICE) $(FILENAME_SIM).elf

clean:
	rm -f *.o
	rm -f *.elf
	rm -f *.hex
	rm -f *.vcd