#include "cyhal.h"
#include "cybsp.h"
#include "cy_retarget_io.h"
#include <FreeRTOS.h>
#include <task.h>
#include <semphr.h>
#include <string.h>
#include "cy_secure_sockets.h"
#include "cy_wcm.h"
#include "cy_wcm_error.h"
#include "tcp_client.h"
#include "ip_addr.h"
#include <inttypes.h>

#define WIFI_INTERFACE_TYPE                   CY_WCM_INTERFACE_TYPE_STA
#define WIFI_SSID                             "Coherent"
#define WIFI_PASSWORD                         "harry0202"
#define WIFI_SECURITY_TYPE                    CY_WCM_SECURITY_WPA2_AES_PSK

/* Maximum number of connection retries to a Wi-Fi network. */
#define MAX_WIFI_CONN_RETRIES                 (10u)

/* Wi-Fi re-connection time interval in milliseconds */
#define WIFI_CONN_RETRY_INTERVAL_MSEC         (1000u)

/* Maximum number of connection retries to the TCP server. */
#define MAX_TCP_SERVER_CONN_RETRIES               (5u)

/* Length of the TCP data packet. */
#define MAX_TCP_DATA_PACKET_LENGTH                (20u)

/* TCP keep alive related macros. */
#define TCP_KEEP_ALIVE_IDLE_TIME_MS               (10000u)
#define TCP_KEEP_ALIVE_INTERVAL_MS                (1000u)
#define TCP_KEEP_ALIVE_RETRY_COUNT                (2u)

#define TCP_SERVER_PORT                           (50007u)
#define ASCII_BACKSPACE                           (0x08)
#define RTOS_TICK_TO_WAIT                         (50u)
#define UART_INPUT_TIMEOUT_MS                     (1u)
#define UART_BUFFER_SIZE                          (50u)

/*******************************************************************************
* Function Prototypes
********************************************************************************/
cy_rslt_t create_tcp_client_socket();
cy_rslt_t connect_to_tcp_server(cy_socket_sockaddr_t address, char *key, bool *send_success);
static cy_rslt_t connect_to_wifi_ap(void);

/*******************************************************************************
* Global Variables
********************************************************************************/
/* TCP client socket handle */
cy_socket_t client_handle;

/* Binary semaphore handle to keep track of TCP server connection. */
SemaphoreHandle_t connect_to_server;

/*******************************************************************************
 * Function Name: tcp_client_task
 *******************************************************************************
 * Summary:
 *  Task used to establish a connection to a remote TCP server and
 *  control the LED state (ON/OFF) based on the command received from TCP server.
 *
 * Parameters:
 *  void *args : Task parameter defined during task creation (unused).
 *
 * Return:
 *  void
 *
 *******************************************************************************/
void tcp_client_task(void *arg)
{

	while(1){
		int msg = 0;
		if(!xQueueReceive(qh, &msg, pdMS_TO_TICKS(10000)))
		{
			printf("Blocked\n");
			continue;
		}
		printf("the keyword is %s\n", detected_keyword);
	    cy_wcm_config_t wifi_config = { .interface = WIFI_INTERFACE_TYPE };

	    /* IP address and TCP port number of the TCP server to which the TCP client
	     * connects to.
	     */
	    cy_socket_sockaddr_t tcp_server_address =
	    {
	        .ip_address.version = CY_SOCKET_IP_VER_V4,
	        .port = TCP_SERVER_PORT
	    };


		cy_rslt_t result ;
	    uint8_t uart_input[UART_BUFFER_SIZE];
	    /* Initialize Wi-Fi connection manager. */
	    result = cy_wcm_init(&wifi_config);

	    if (result != CY_RSLT_SUCCESS)
	    {
	        printf("Wi-Fi Connection Manager initialization failed! Error code: 0x%08"PRIx32"\n", (uint32_t)result);
	        CY_ASSERT(0);
	    }
	    printf("Wi-Fi Connection Manager initialized.\r\n");


		/* Connect to Wi-Fi AP */
		result = connect_to_wifi_ap();
		if(result!= CY_RSLT_SUCCESS )
		{
			printf("\n Failed to connect to Wi-Fi AP! Error code: 0x%08"PRIx32"\n", (uint32_t)result);
			CY_ASSERT(0);
		}

	    /* Create a binary semaphore to keep track of TCP server connection. */
	    connect_to_server = xSemaphoreCreateBinary();

	    /* Give the semaphore so as to connect to TCP server.  */
	    xSemaphoreGive(connect_to_server);

	    /* Initialize secure socket library. */
	    result = cy_socket_init();

	    if (result != CY_RSLT_SUCCESS)
	    {
	        printf("Secure Socket initialization failed!\n");
	        CY_ASSERT(0);
	    }
	    printf("Secure Socket initialized\n");

	    bool send_success = 0;
	    while(!send_success)
	    {
	        /* Wait till semaphore is acquired so as to connect to a TCP server. */
	        xSemaphoreTake(connect_to_server, portMAX_DELAY);

	        printf("Connect to TCP server\n");

	        /* Prevent system from entering deep sleep mode
	         * when receiving data from UART.
	         */
	        cyhal_syspm_lock_deepsleep();

	        /* Clear the UART input buffer. */
	        memset(uart_input, 0, UART_BUFFER_SIZE);
	        memcpy(uart_input, "172.20.10.4", strlen("172.20.10.4"));
	        /* Read the TCP server's IPv4 address from  the user via the
	         * UART terminal.
	         */
	        //read_uart_input(uart_input);

	        /* Allow system to enter deep sleep mode. */
	        cyhal_syspm_unlock_deepsleep();

	        ip4addr_aton((char *)uart_input,
	                     (ip4_addr_t *)&tcp_server_address.ip_address.ip.v4);

	        /* Connect to the TCP server. If the connection fails, retry
	         * to connect to the server for MAX_TCP_SERVER_CONN_RETRIES times.
	         */
	        printf("Connecting to TCP Server (IP Address: %s, Port: %d)\n\n",
	                      ip4addr_ntoa((const ip4_addr_t *)&tcp_server_address.ip_address.ip.v4),
	                      TCP_SERVER_PORT);

	        result = connect_to_tcp_server(tcp_server_address, detected_keyword, &send_success);

	        if(result != CY_RSLT_SUCCESS)
	        {
	            printf("Failed to connect to TCP server.\n");

	            /* Give the semaphore so as to connect to TCP server.  */
	            xSemaphoreGive(connect_to_server);
	        }
	    }
	    printf("Finished Infinite While Loop\n\r");
	    result = cy_wcm_disconnect_ap();

	    if(result != CY_RSLT_SUCCESS){
	    	printf("Disconnected AP fail. \n");
	    }
	    else{
	    	printf("Disconnected AP successful! \n");
	    }

	    //de-initialize the wcm
	    cy_wcm_deinit();
	    vTaskDelete(NULL);
	}

 }

/*******************************************************************************
 * Function Name: connect_to_wifi_ap()
 *******************************************************************************
 * Summary:
 *  Connects to Wi-Fi AP using the user-configured credentials, retries up to a
 *  configured number of times until the connection succeeds.
 *
 *******************************************************************************/
cy_rslt_t connect_to_wifi_ap(void)
{
    cy_rslt_t result;

    /* Variables used by Wi-Fi connection manager.*/
    cy_wcm_connect_params_t wifi_conn_param;

    cy_wcm_ip_address_t ip_address;

     /* Set the Wi-Fi SSID, password and security type. */
    memset(&wifi_conn_param, 0, sizeof(cy_wcm_connect_params_t));
    memcpy(wifi_conn_param.ap_credentials.SSID, WIFI_SSID, sizeof(WIFI_SSID));
    memcpy(wifi_conn_param.ap_credentials.password, WIFI_PASSWORD, sizeof(WIFI_PASSWORD));
    wifi_conn_param.ap_credentials.security = WIFI_SECURITY_TYPE;

    printf("Connecting to Wi-Fi Network: %s\n", WIFI_SSID);

    /* Join the Wi-Fi AP. */
    for(uint32_t conn_retries = 0; conn_retries < MAX_WIFI_CONN_RETRIES; conn_retries++ )
    {
        result = cy_wcm_connect_ap(&wifi_conn_param, &ip_address);

        if(result == CY_RSLT_SUCCESS)
        {
            printf("Successfully connected to Wi-Fi network '%s'.\n",
                                wifi_conn_param.ap_credentials.SSID);
            printf("IP Address Assigned: %s\n",
                    ip4addr_ntoa((const ip4_addr_t *)&ip_address.ip.v4));
            return result;
        }

        printf("Connection to Wi-Fi network failed with error code %d."
               "Retrying in %d ms...\n", (int)result, WIFI_CONN_RETRY_INTERVAL_MSEC);

        vTaskDelay(pdMS_TO_TICKS(WIFI_CONN_RETRY_INTERVAL_MSEC));
    }

    /* Stop retrying after maximum retry attempts. */
    printf("Exceeded maximum Wi-Fi connection attempts\n");

    return result;
}

/*******************************************************************************
 * Function Name: create_tcp_client_socket
 *******************************************************************************
 * Summary:
 *  Function to create a socket and set the socket options
 *  to set call back function for handling incoming messages, call back
 *  function to handle disconnection.
 *
 *******************************************************************************/
cy_rslt_t create_tcp_client_socket()
{
    cy_rslt_t result;

    /* TCP keep alive parameters. */
    int keep_alive = 1;
    uint32_t keep_alive_interval = TCP_KEEP_ALIVE_INTERVAL_MS;
    uint32_t keep_alive_count    = TCP_KEEP_ALIVE_RETRY_COUNT;
    uint32_t keep_alive_idle_time = TCP_KEEP_ALIVE_IDLE_TIME_MS;

    /* Create a new secure TCP socket. */
    result = cy_socket_create(CY_SOCKET_DOMAIN_AF_INET, CY_SOCKET_TYPE_STREAM,
                              CY_SOCKET_IPPROTO_TCP, &client_handle);

    if (result != CY_RSLT_SUCCESS)
    {
        printf("Failed to create socket!\n");
        return result;
    }


    /* Set the TCP keep alive interval. */
    result = cy_socket_setsockopt(client_handle, CY_SOCKET_SOL_TCP,
                                  CY_SOCKET_SO_TCP_KEEPALIVE_INTERVAL,
                                  &keep_alive_interval, sizeof(keep_alive_interval));
    if(result != CY_RSLT_SUCCESS)
    {
        printf("Set socket option: CY_SOCKET_SO_TCP_KEEPALIVE_INTERVAL failed\n");
        return result;
    }

    /* Set the retry count for TCP keep alive packet. */
    result = cy_socket_setsockopt(client_handle, CY_SOCKET_SOL_TCP,
                                  CY_SOCKET_SO_TCP_KEEPALIVE_COUNT,
                                  &keep_alive_count, sizeof(keep_alive_count));
    if(result != CY_RSLT_SUCCESS)
    {
        printf("Set socket option: CY_SOCKET_SO_TCP_KEEPALIVE_COUNT failed\n");
        return result;
    }

    /* Set the network idle time before sending the TCP keep alive packet. */
    result = cy_socket_setsockopt(client_handle, CY_SOCKET_SOL_TCP,
                                  CY_SOCKET_SO_TCP_KEEPALIVE_IDLE_TIME,
                                  &keep_alive_idle_time, sizeof(keep_alive_idle_time));
    if(result != CY_RSLT_SUCCESS)
    {
        printf("Set socket option: CY_SOCKET_SO_TCP_KEEPALIVE_IDLE_TIME failed\n");
        return result;
    }

    /* Enable TCP keep alive. */
    result = cy_socket_setsockopt(client_handle, CY_SOCKET_SOL_SOCKET,
                                      CY_SOCKET_SO_TCP_KEEPALIVE_ENABLE,
                                          &keep_alive, sizeof(keep_alive));
    if(result != CY_RSLT_SUCCESS)
    {
        printf("Set socket option: CY_SOCKET_SO_TCP_KEEPALIVE_ENABLE failed\n");
        return result;
    }

    return result;
}

/*******************************************************************************
 * Function Name: connect_to_tcp_server
 *******************************************************************************
 * Summary:
 *  Function to connect to TCP server.
 *
 * Parameters:
 *  cy_socket_sockaddr_t address: Address of TCP server socket
 *
 * Return:
 *  cy_result result: Result of the operation
 *
 *******************************************************************************/
cy_rslt_t connect_to_tcp_server(cy_socket_sockaddr_t address, char *key, bool *send_success)
{
	cy_rslt_t result = CY_RSLT_MODULE_SECURE_SOCKETS_TIMEOUT;
    cy_rslt_t conn_result;
    for(uint32_t conn_retries = 0; conn_retries < MAX_TCP_SERVER_CONN_RETRIES; conn_retries++){
        /* Create a TCP socket */
        conn_result = create_tcp_client_socket();
        if(conn_result != CY_RSLT_SUCCESS){
            printf("Socket creation failed!\n");
            CY_ASSERT(0);
        }
        conn_result = cy_socket_connect(client_handle, &address, sizeof(cy_socket_sockaddr_t));
        if (conn_result == CY_RSLT_SUCCESS){
            printf("============================================================\n");
            printf("Connected to TCP server\n");
            uint32_t bytes_sent = 0;

            result = cy_socket_send(client_handle, key, strlen(key), CY_SOCKET_FLAGS_NONE, &bytes_sent);
            printf("Send MSG to server\n\r");
            if (result != CY_RSLT_SUCCESS)
            {
                printf("Failed to send message to the server!\n");
                return result;
            }

            //delete the socket
            cy_socket_disconnect(client_handle, 0);			/* Disconnect the TCP client. */
            cy_socket_delete(client_handle);				/* Free the resources allocated to the socket. */
            xSemaphoreGive(connect_to_server);				/* Give the semaphore so as to connect to TCP server. */
            printf("Delete the socket successfully\n\r");
            *send_success = 1;
            return conn_result;
        }
        printf("Could not connect to TCP server. Error code: 0x%08"PRIx32"\n", (uint32_t)result);
        printf("Trying to reconnect to TCP server... Please check if the server is listening\n");
        cy_socket_delete(client_handle);
    }
     printf("Exceeded maximum connection attempts to the TCP server\n");
     return result;
}
