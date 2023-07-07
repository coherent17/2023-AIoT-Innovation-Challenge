#include "cyhal.h"
#include "cybsp.h"
#include "cy_retarget_io.h"
#include "stdlib.h"

#include "cyberon_asr.h"

/* FreeRTOS header file. */
#include <FreeRTOS.h>
#include <task.h>
#include "queue.h"

/* TCP client task header file. */
#include "tcp_client.h"

#define FRAME_SIZE                  (480u)
#define SAMPLE_RATE_HZ              (16000u)
#define DECIMATION_RATE             (96u)
#define AUDIO_SYS_CLOCK_HZ          (24576000u)
#define PDM_DATA                    (P10_5)
#define PDM_CLK                     (P10_4)

void pdm_pcm_isr_handler(void *arg, cyhal_pdm_pcm_event_t event);
void clock_init(void);

void asr_callback(const char *function, char *message, char *parameter);
void voiceRecognitionTask(void *pvParameters);

volatile bool pdm_pcm_flag = false;
int16_t pdm_pcm_ping[FRAME_SIZE] = {0};
int16_t pdm_pcm_pong[FRAME_SIZE] = {0};
int16_t *pdm_pcm_buffer = &pdm_pcm_ping[0];
cyhal_pdm_pcm_t pdm_pcm;
cyhal_clock_t   audio_clock;
cyhal_clock_t   pll_clock;

/* RTOS related macros. */
#define TCP_CLIENT_TASK_STACK_SIZE        (5 * 1024)
#define TCP_CLIENT_TASK_PRIORITY          (2)

const cyhal_pdm_pcm_cfg_t pdm_pcm_cfg = 
{
    .sample_rate     = SAMPLE_RATE_HZ,
    .decimation_rate = DECIMATION_RATE,
    .mode            = CYHAL_PDM_PCM_MODE_LEFT, 
    .word_length     = 16,  /* bits */
    .left_gain       = CYHAL_PDM_PCM_MAX_GAIN,   /* dB */
    .right_gain      = CYHAL_PDM_PCM_MAX_GAIN,   /* dB */
};

// Global Queue Handle
QueueHandle_t qh = 0;

int main(void)
{
    cy_rslt_t result;
    uint64_t uid;

    result = cybsp_init() ;
    if(result != CY_RSLT_SUCCESS)
    {
        CY_ASSERT(0);
    }

    __enable_irq();
    clock_init();
    cy_retarget_io_init(CYBSP_DEBUG_UART_TX, CYBSP_DEBUG_UART_RX, CY_RETARGET_IO_BAUDRATE);

    cyhal_pdm_pcm_init(&pdm_pcm, PDM_DATA, PDM_CLK, &audio_clock, &pdm_pcm_cfg);
    cyhal_pdm_pcm_register_callback(&pdm_pcm, pdm_pcm_isr_handler, NULL);
    cyhal_pdm_pcm_enable_event(&pdm_pcm, CYHAL_PDM_PCM_ASYNC_COMPLETE, CYHAL_ISR_PRIORITY_DEFAULT, true);
    cyhal_pdm_pcm_start(&pdm_pcm);
    cyhal_pdm_pcm_read_async(&pdm_pcm, pdm_pcm_buffer, FRAME_SIZE);

    printf("\x1b[2J\x1b[;H");
    printf("===== Cyberon DSpotter Demo =====\r\n");

    uid = Cy_SysLib_GetUniqueId();
    printf("uniqueIdHi: 0x%08lX, uniqueIdLo: 0x%08lX\r\n", (uint32_t)(uid >> 32), (uint32_t)(uid << 32 >> 32));

    if(!cyberon_asr_init(asr_callback))
    {
    	while(1);
    }

    printf("\r\nAwaiting voice input trigger command (\"你好\"):\r\n");
    qh = xQueueCreate(1, sizeof(int));
    xTaskCreate(tcp_client_task, "TCP Client Task", 5 * 1024, NULL, tskIDLE_PRIORITY + 1, NULL);
    xTaskCreate(voiceRecognitionTask, "Voice Recognition Task", 5 * 1024, NULL, tskIDLE_PRIORITY, NULL);


    // Start the FreeRTOS scheduler
    vTaskStartScheduler();

    /* Should never get here. */
    CY_ASSERT(0);
}

void pdm_pcm_isr_handler(void *arg, cyhal_pdm_pcm_event_t event)
{
    static bool ping_pong = false;

    (void) arg;
    (void) event;

    if(ping_pong)
    {
        cyhal_pdm_pcm_read_async(&pdm_pcm, pdm_pcm_ping, FRAME_SIZE);
        pdm_pcm_buffer = &pdm_pcm_pong[0];
    }
    else
    {
        cyhal_pdm_pcm_read_async(&pdm_pcm, pdm_pcm_pong, FRAME_SIZE);
        pdm_pcm_buffer = &pdm_pcm_ping[0]; 
    }

    ping_pong = !ping_pong;
    pdm_pcm_flag = true;
}

void clock_init(void)
{
	cyhal_clock_reserve(&pll_clock, &CYHAL_CLOCK_PLL[0]);
    cyhal_clock_set_frequency(&pll_clock, AUDIO_SYS_CLOCK_HZ, NULL);
    cyhal_clock_set_enabled(&pll_clock, true, true);

    cyhal_clock_reserve(&audio_clock, &CYHAL_CLOCK_HF[1]);

    cyhal_clock_set_source(&audio_clock, &pll_clock);
    cyhal_clock_set_enabled(&audio_clock, true, true);
}

void asr_callback(const char *function, char *message, char *parameter)
{
	printf("[%s]%s(%s)\r\n", function, message, parameter);
}

void voiceRecognitionTask(void *pvParameters)
{
	while (1)
    {
        if (pdm_pcm_flag)
        {
        	pdm_pcm_flag = false;
            cyberon_asr_process(pdm_pcm_buffer, FRAME_SIZE);
        }
    }
}
