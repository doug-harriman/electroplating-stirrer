#include "hw.h"

#include <util/delay.h>
#include <avr/sleep.h>

#ifdef SIMULATION
// Simulation configuration
#include "simavr/sim/avr/avr_mcu_section.h"
AVR_MCU(F_CPU, DEVICE);
AVR_MCU_VCD_PORT_PIN('B', PIN0, "PWM");
#endif // SIMULATION

int main(void)
{
    hw_init();

    // Servo
    // http://192.168.0.120:8800/part/1/#
    // Servo basline freq is 50 Hz.
    uint16_t period_us = 20000; // [usec]

    // Spec values
    // uint16_t period_min_us = 900;
    // uint16_t period_max_us = 2100;

    // Practical values for 5V driver per test.
    uint16_t period_mid_us = 1500; // 1.5ms is no motion

    // TODO: Spec says 100 us either side of mid
    // TODO: Get this code posted, then link servo inventree to code.
    uint16_t period_mag_us = 300; // 300 us either direction from mid.
    uint16_t period_min_us = period_mid_us - period_mag_us;
    // uint16_t period_max_us = period_mid_us + period_mag_us;

    // Initial PWM period
    uint16_t period_on_us = 1500;

    while (1)
    {
        // Start conversion
        ADCSRA |= (1 << ADSC);

        // Set PWM based on last read.
        // The PWM value is held for 5 readings: 50Hz/5 = 10Hz update
        for (uint8_t i = 0; i < 5; i++)
        {
            // On time
            PORTB |= (1 << PWM_PIN);
            _delay_loop_2(period_on_us >> 2);

            // Off time
            PORTB &= ~(1 << PWM_PIN);
            _delay_loop_2((period_us - period_on_us) >> 2);
        }

        // Read the ADC value
        uint8_t adc_val = ADCH;

        // Update period
        period_on_us = period_min_us + adc_val;
    }

    // Exit
    sleep_cpu();
}
