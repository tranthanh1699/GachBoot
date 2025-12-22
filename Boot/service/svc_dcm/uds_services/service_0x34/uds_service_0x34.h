#ifndef UDS_SERVICE_0X34_H
#define UDS_SERVICE_0X34_H

#include "dev_common.h"
#include "dcmdsp/dcmdsp.h"

typedef struct {
	bool active;                       /* Download session is active */
	uint8_t format_identifier;         /* Raw length format identifier from request */
	uint32_t start_address;            /* Requested download start address */
	uint32_t total_size;               /* Total number of bytes requested */
	uint32_t bytes_transferred;        /* Bytes already transferred via 0x36 */
	uint32_t max_block_length;         /* Max block length the server accepts */
	uint8_t expected_block_sequence;   /* Next expected blockSequenceCounter for 0x36 */
} uds_download_context_t;

/**
 * @brief Service 0x34 handler - Request Download
 * @param message Request and response message structure
 * @param error_code NRC if error (output)
 * @return Std_ReturnType E_OK (positive response), E_NOT_OK (negative response), DCM_E_PENDING (pending)
 */
Std_ReturnType uds_service_0x34_handler(const uds_message_t *message, ErrorCode_t *error_code);

const uds_download_context_t* uds_download_get_context(void);
void uds_download_reset_context(void);

#endif // UDS_SERVICE_0X34_H
