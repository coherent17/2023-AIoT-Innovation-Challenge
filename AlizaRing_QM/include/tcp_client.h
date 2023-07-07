#ifndef TCP_CLIENT_H_
#define TCP_CLIENT_H_

#define MAX_ARRAY_LENGTH (50u)

//for stored the detected keyword in Voice Recognition Task
extern char detected_keyword[MAX_ARRAY_LENGTH];

//for Queue Message Method
extern QueueHandle_t qh;

void tcp_client_task(void *arg);

#endif /* TCP_CLIENT_H_ */
