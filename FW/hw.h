#ifndef _HW_H_
#define _HW_H_

#include <avr/io.h>

#define PIN_SERVO (PB2)
#define PIN_POT_100k (PB3)

// Initializes the hardware
void hw_init(void);

#endif // _HW_H_
