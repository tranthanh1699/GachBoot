#include "bl_state_machine.h"

bl_session_state_t bl_state_machine_get_state(const bl_session_t *session)
{
    if (session == (const bl_session_t *)0)
    {
        return BL_SESSION_STATE_ERROR;
    }

    return session->state;
}
