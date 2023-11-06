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

    // Configure ATTiny85 pin PB0 as output
    // DDRB |= (1 << PB0);
    DDRB |= (1 << PWM_PIN);

    // ADC configuration
    // Configure PB2 for analog input.
    DDRB &= ~(1 << DDB2);

    // Select ADC channel 2.
    // Zeros in REFSx uses Vcc as reference
    ADMUX |= (1 << ADLAR); // ADLAR = 1, left adjust result

    // Single ended conversion on PB2, bit 0 set.
    ADMUX |= 1;

    // Enable conversions
    ADCSRA |= (1 << ADEN);
}