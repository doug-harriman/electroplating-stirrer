#include "hw.h"

void hw_init(void)
{
    // System clock is 1MHz, tick is 1us.
    // clk_io = system clock
    // Per datasheet, page 74, fOCnxPWM = clk_io / (prescaler * 256)
    // PWM clock period = 1 usec * 64 * 256 = 16.384 ms
    // PWM clock freq = 61 Hz.

    // Configure timer0 to fast PWM mode at 50Hz
    // TCCR0A |= (1 << WGM01) | (1 << WGM00); // Set timer0 to fast PWM mode
    // TCCR0A |= (1 << COM0A1);               // Clear OC0A on compare match, set at BOTTOM
    // TCCR0B |= (1 << CS01) | (1 << CS00);   // Set prescaler to 64
    // OCR0A = 0; // No output initially

    // MCU: ATtiny85-20P (U1)
    // Datasheet: http://ww1.microchip.com/downloads/en/DeviceDoc/atmel-2586-avr-8-bit-microcontroller-attiny25-attiny45-attiny85_datasheet.pdf

    // Net SERVO: ATtiny85-20P (U1) pin 7 -> SERVO (J1) pin 2
    // ATtiny85-20P: pin 7 = PB2
    // PB2 as output
    DDRB |= (1 << PIN_SERVO);

    // Net V-POT: ATtiny85-20P (U1) pin 2 <- POT 100k (RV1) pin 2
    // ATtiny85-20P: pin 2 = XTAL1/PB3
    // PB3 as input
    DDRB &= ~(1 << PIN_POT_100k);

    // Configure PIN_POT_100k as ADC input
    // Select ADC channel 2.
    // Zeros in REFSx uses Vcc as reference
    ADMUX |= (1 << ADLAR); // ADLAR = 1, left adjust result

    // Select PB3 (ADC3)
    ADMUX |= (1 << MUX0) | (1 << MUX1); //

    // Enable conversions
    ADCSRA |= (1 << ADEN);
}