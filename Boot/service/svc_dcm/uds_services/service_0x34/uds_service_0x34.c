#include "uds_service_0x34.h"
#include "svc_dcm.h"
#include "dcmdsl/dcmdsl.h"
#include "dcm_service_access.h"
#include "Memory_Layout_Config.h"
#include <string.h>
#include "../service_0x27/uds_service_0x27.h"

CONFIG_LOG_TAG(UDS_0x34, true)

#define UDS_SERVICE_ID_REQUEST_DOWNLOAD   0x34u

static uds_download_context_t download_ctx = {0};

static uint32_t parse_big_endian(const uint8_t *data, uint8_t len)
{
	uint32_t value = 0;
	for (uint8_t i = 0; i < len; i++) {
		value = (value << 8) | data[i];
	}
	return value;
}

const uds_download_context_t* uds_download_get_context(void)
{
	return &download_ctx;
}

void uds_download_reset_context(void)
{
	memset(&download_ctx, 0, sizeof(download_ctx));
}

Std_ReturnType uds_service_0x34_handler(const uds_message_t *message, ErrorCode_t *error_code)
{
	if (message->request_len < 4u) {
		*error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
		return E_NOT_OK;
	}

	const uint8_t data_format_identifier = message->request[1];
	const uint8_t format_identifier = message->request[2];
	const uint8_t addr_len = (format_identifier >> 4) & 0x0Fu;
	const uint8_t size_len = format_identifier & 0x0Fu;

	if (addr_len == 0u || size_len == 0u || addr_len > 4u || size_len > 4u) {
		*error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
		return E_NOT_OK;
	}

	const uint16_t expected_len = (uint16_t)(3u + addr_len + size_len);
	if (message->request_len != expected_len) {
		*error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
		return E_NOT_OK;
	}

	if (data_format_identifier != 0x00u) {
		*error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
		return E_NOT_OK;
	}

	const uint32_t start_address = parse_big_endian(&message->request[3], addr_len);
	const uint32_t total_size = parse_big_endian(&message->request[3u + addr_len], size_len);

	if (total_size == 0u) {
		*error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
		return E_NOT_OK;
	}

	const uint8_t current_session = dcmdsl_get_session();
	const uint8_t current_security_level = uds_security_get_active_level();
	const uint32_t session_mask = dcm_service_get_session_mask(current_session);
	const uint32_t security_mask = dcm_service_get_security_mask(current_security_level);

	if (dcm_service_check_access(UDS_SERVICE_ID_REQUEST_DOWNLOAD, session_mask, security_mask, error_code) != E_OK) {
		return E_NOT_OK;
	}

	/* Validate address and size using generated config helper */
	if (!is_address_valid_for_download(start_address, total_size)) {
		*error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
		return E_NOT_OK;
	}

	uint32_t max_block_length = (total_size < DOWNLOAD_MAX_BLOCK_LENGTH_BYTES) ? total_size : DOWNLOAD_MAX_BLOCK_LENGTH_BYTES;
	uint8_t max_block_length_size = 1u;
	if (max_block_length > 0xFFFFu) {
		max_block_length_size = 4u;
	} else if (max_block_length > 0xFFu) {
		max_block_length_size = 2u;
	}

	uds_download_reset_context();
	download_ctx.active = true;
	download_ctx.format_identifier = format_identifier;
	download_ctx.start_address = start_address;
	download_ctx.total_size = total_size;
	download_ctx.bytes_transferred = 0u;
	download_ctx.max_block_length = max_block_length;
	download_ctx.expected_block_sequence = 1u;

	message->response[0] = max_block_length_size;  /* lengthFormatIdentifier for response */
	for (uint8_t i = 0; i < max_block_length_size; i++) {
		uint8_t shift = (uint8_t)((max_block_length_size - 1u - i) * 8u);
		message->response[1u + i] = (uint8_t)((max_block_length >> shift) & 0xFFu);
	}

	*(message->response_len) = (uint16_t)(1u + max_block_length_size);

	DBG_OUT_I("RequestDownload accepted: addr=0x%08X, size=0x%08X, maxBlock=%u (lenBytes=%u)",
			  start_address, total_size, max_block_length, max_block_length_size);

	return E_OK;
}