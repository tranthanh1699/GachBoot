#!/usr/bin/env python3
"""
Routine Module - Validation and Code Generation for UDS Routines (Service 0x31)
"""

from typing import Dict, List, Tuple
from datetime import datetime


def validate_routine_config(routine: Dict) -> Tuple[bool, str]:
    """Validate a single routine configuration"""
    
    # Required fields
    required_fields = ['rid', 'routine_name', 'callback_function', 
                      'supported_subfunctions', 'supported_sessions']
    for field in required_fields:
        if field not in routine:
            return False, f"Missing required field: {field}"
    
    # Validate RID format
    rid_str = routine['rid']
    if not rid_str.startswith('0x'):
        return False, f"RID must start with '0x': {rid_str}"
    
    try:
        rid_val = int(rid_str, 16)
        if rid_val < 0 or rid_val > 0xFFFF:
            return False, f"RID must be in range 0x0000-0xFFFF: {rid_str}"
    except ValueError:
        return False, f"Invalid RID hex format: {rid_str}"
    
    # Validate subfunctions
    valid_subfunctions = ['START', 'STOP', 'REQUEST_RESULTS']
    for subfunc in routine['supported_subfunctions']:
        if subfunc not in valid_subfunctions:
            return False, f"Invalid subfunction: {subfunc}. Must be one of {valid_subfunctions}"
    
    # Validate sessions
    if not routine['supported_sessions']:
        return False, "At least one session must be specified"
    
    return True, "OK"


def validate_routines(routines: List[Dict]) -> Tuple[bool, List[str]]:
    """Validate all routine configurations"""
    errors = []
    rid_set = set()
    
    for i, routine in enumerate(routines):
        # Validate individual routine
        valid, msg = validate_routine_config(routine)
        if not valid:
            errors.append(f"Routine [{i}]: {msg}")
            continue
        
        # Check for duplicate RIDs
        rid = routine['rid']
        if rid in rid_set:
            errors.append(f"Routine [{i}]: Duplicate RID {rid}")
        rid_set.add(rid)
    
    return len(errors) == 0, errors


def generate_routine_header(routines: List[Dict], output_dir: str) -> str:
    """Generate Routine_PBCfg.h header file"""
    
    # Generate session name to mask mapping
    session_masks = {
        'DCM_DEFAULT_SESSION': 'DCM_DEFAULT_SESSION_MASK',
        'DCM_PROGRAMMING_SESSION': 'DCM_PROGRAMMING_SESSION_MASK',
        'DCM_EXTENDED_SESSION': 'DCM_EXTENDED_SESSION_MASK'
    }
    
    # Header guard
    content = f"""#ifndef ROUTINE_PBCFG_H
#define ROUTINE_PBCFG_H

/**
 * @file Routine_PBCfg.h
 * @brief UDS Routine Control Configuration (Service 0x31)
 * @date Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * 
 * This file contains routine registry and callback declarations
 */

#include <stdint.h>
#include <stdbool.h>

/* ========================================================================== */
/*                           Forward Declarations                             */
/* ========================================================================== */

#ifndef STD_TYPES_H
typedef uint8_t Std_ReturnType;
#define E_OK        0x00u
#define E_NOT_OK    0x01u
#define DCM_E_PENDING    0x10u
#endif

/* ========================================================================== */
/*                         Routine Control Constants                          */
/* ========================================================================== */

/* Routine Control Sub-functions (ISO 14229-1) */
#define UDS_ROUTINE_CONTROL_START               0x01
#define UDS_ROUTINE_CONTROL_STOP                0x02
#define UDS_ROUTINE_CONTROL_REQUEST_RESULTS     0x03

/* ========================================================================== */
/*                              Type Definitions                              */
/* ========================================================================== */

/**
 * @brief Routine control callback function type
 * @param sub_function Sub-function (0x01=Start, 0x02=Stop, 0x03=RequestResults)
 * @param option_record Optional parameters (input)
 * @param option_record_len Length of option record
 * @param status_record Status/results (output)
 * @param status_record_len Length of status record (output)
 * @return Std_ReturnType E_OK, E_NOT_OK, DCM_E_PENDING
 */
typedef Std_ReturnType (*uds_routine_callback_t)(
    uint8_t sub_function,
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/**
 * @brief Routine control entry structure
 */
typedef struct {{
    uint16_t rid;                    /**< Routine Identifier */    uint8_t supported_subfunctions;  /**< Bitmask: bit0=START, bit1=STOP, bit2=REQUEST_RESULTS */
    uint16_t start_option_len;       /**< Expected option_record length for START (0=variable) */
    uint16_t start_status_len;       /**< Expected status_record length for START */
    uint16_t stop_option_len;        /**< Expected option_record length for STOP (0=variable) */
    uint16_t stop_status_len;        /**< Expected status_record length for STOP */
    uint16_t results_option_len;     /**< Expected option_record length for REQUEST_RESULTS (0=variable) */
    uint16_t results_status_len;     /**< Expected status_record length for REQUEST_RESULTS */    uds_routine_callback_t callback; /**< Routine handler callback */
    uint32_t session_mask;           /**< Allowed sessions bitmask */
    uint32_t security_mask;          /**< Required security bitmask */
}} uds_routine_entry_t;

/* ========================================================================== */
/*                         Routine Callback Declarations                      */
/* ========================================================================== */

"""
    
    # Generate per-subfunction callback declarations
    for routine in routines:
        base_callback = routine['callback_function']
        desc = routine.get('description', '')
        subfuncs = routine['supported_subfunctions']
        subfunction_params = routine.get('subfunction_parameters', {})
        
        content += f"""/**
 * @brief {desc}
 */
"""
        
        # Declare callback for each supported subfunction
        for sf in subfuncs:
            sf_lower = sf.lower()
            params = subfunction_params.get(sf, {})
            opt_desc = params.get('option_record_description', 'N/A')
            stat_desc = params.get('status_record_description', 'Status')
            
            content += f"""/**
 * @brief {desc} - {sf}
 * @param option_record {opt_desc}
 * @param option_record_len Length of option record
 * @param status_record {stat_desc}
 * @param status_record_len Length of status record (output)
 * @return E_OK on success, E_NOT_OK on failure
 */
extern Std_ReturnType {base_callback}_{sf_lower}(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

"""
    
    # Generate routine name constants
    content += """/* ========================================================================== */
/*                           Routine Name Constants                           */
/* ========================================================================== */

"""
    
    for routine in routines:
        rid = routine['rid']
        name = routine['routine_name']
        desc = routine.get('description', '')
        content += f"#define {name:<50} {rid}  /**< {desc} */\n"
    
    # Generate record length definitions
    content += """
/* ========================================================================== */
/*                    Record Length Definitions                               */
/* ========================================================================== */

"""
    
    for routine in routines:
        name = routine['routine_name']
        subfunction_params = routine.get('subfunction_parameters', {})
        
        for sf in routine['supported_subfunctions']:
            params = subfunction_params.get(sf, {})
            opt_len = params.get('option_record_length', 0)
            stat_len = params.get('status_record_length', 0)
            
            # Define for option record length (0 = variable/optional)
            content += f"#define {name}_{sf}_OPTION_LENGTH    {opt_len}U"
            if opt_len == 0:
                content += "  /**< Variable or no input */"
            content += "\n"
            
            # Define for status record length
            content += f"#define {name}_{sf}_STATUS_LENGTH    {stat_len}U\n"
    
    # Generate registry access functions
    content += """
/* ========================================================================== */
/*                         Registry Access Functions                          */
/* ========================================================================== */

/**
 * @brief Find routine entry in registry
 * @param rid Routine Identifier
 * @return Pointer to routine entry, or NULL if not found
 */
const uds_routine_entry_t* uds_routine_find_entry(uint16_t rid);

/**
 * @brief Validate option_record length for routine
 * @param entry Routine entry
 * @param sub_function Sub-function (0x01=START, 0x02=STOP, 0x03=REQUEST_RESULTS)
 * @param option_record_len Actual length from request
 * @return true if valid, false otherwise
 * @note If expected length is 0, any length is accepted (variable/optional)
 */
bool uds_routine_validate_option_length(const uds_routine_entry_t *entry, 
                                         uint8_t sub_function, 
                                         uint16_t option_record_len);

/**
 * @brief Get routine registry
 * @param count Output: number of entries
 * @return Pointer to routine registry
 */
const uds_routine_entry_t* uds_routine_get_registry(uint16_t *count);

#endif /* ROUTINE_PBCFG_H */
"""
    
    return content


def generate_routine_source(routines: List[Dict], sessions: List[Dict], 
                           security_levels: List[Dict], output_dir: str) -> str:
    """Generate Routine_PBCfg.c source file"""
    
    # Build session mask mapping
    session_name_to_mask = {}
    for session in sessions:
        session_name = session['session_name']
        session_name_to_mask[session_name] = f"{session_name}_MASK"
    
    # Build security level mask
    def build_security_mask(security_list: List[int]) -> str:
        if not security_list:
            return "0xFFFFFFFF"  # All levels allowed
        mask_parts = [f"(1U << {level}U)" for level in security_list]
        return " | ".join(mask_parts) if mask_parts else "0x00000000"
    
    # Build session mask
    def build_session_mask(session_list: List[str]) -> str:
        if not session_list:
            return "0x00000000"
        mask_parts = [session_name_to_mask.get(s, f"{s}_MASK") for s in session_list]
        return " | ".join(mask_parts)
    
    content = f"""/**
 * @file Routine_PBCfg.c
 * @brief UDS Routine Control Configuration Implementation
 * @date Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * 
 * Auto-generated from gachboot_config.json
 * DO NOT EDIT MANUALLY
 */

#include "Routine_PBCfg.h"
#include "DCM_Session_PBCfg.h"
#include "Security_PBCfg.h"

/* ========================================================================== */
/*                         Routine Wrapper Implementations                    */
/* ========================================================================== */

"""
    
    # Generate wrapper functions for each routine
    for routine in routines:
        base_callback = routine['callback_function']
        subfuncs = routine['supported_subfunctions']
        subfunction_params = routine.get('subfunction_parameters', {})
        
        content += f"""/**
 * @brief Wrapper function for routine {routine['rid']} - {routine['routine_name']}
 */
static Std_ReturnType {base_callback}(
    uint8_t sub_function,
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len)
{{
"""
        
        # Generate switch statement for subfunctions
        content += """    switch (sub_function) {
"""
        
        for sf in subfuncs:
            sf_lower = sf.lower()
            sf_macro = f"UDS_ROUTINE_CONTROL_{sf}"
            
            content += f"""        case {sf_macro}:
            return {base_callback}_{sf_lower}(option_record, option_record_len,
                                              status_record, status_record_len);
"""
        
        content += """        default:
            return E_NOT_OK;
    }
}

"""
    
    content += """/* ========================================================================== */
/*                          Routine Registry Table                            */
/* ========================================================================== */

static const uds_routine_entry_t routine_registry[] = {
"""
    
    # Generate routine entries
    for routine in routines:
        rid = routine['rid']
        callback = routine['callback_function']
        session_mask = build_session_mask(routine['supported_sessions'])
        security_mask = build_security_mask(routine.get('required_security_levels', []))
        desc = routine.get('description', '')
        subfuncs = routine['supported_subfunctions']
        subfunction_params = routine.get('subfunction_parameters', {})
        
        # Build supported subfunctions bitmask
        sf_bitmask = 0
        if 'START' in subfuncs:
            sf_bitmask |= (1 << 0)
        if 'STOP' in subfuncs:
            sf_bitmask |= (1 << 1)
        if 'REQUEST_RESULTS' in subfuncs:
            sf_bitmask |= (1 << 2)
        
        # Get record lengths for each subfunction
        start_params = subfunction_params.get('START', {})
        stop_params = subfunction_params.get('STOP', {})
        results_params = subfunction_params.get('REQUEST_RESULTS', {})
        
        start_opt_len = start_params.get('option_record_length', 0)
        start_stat_len = start_params.get('status_record_length', 0)
        stop_opt_len = stop_params.get('option_record_length', 0)
        stop_stat_len = stop_params.get('status_record_length', 0)
        results_opt_len = results_params.get('option_record_length', 0)
        results_stat_len = results_params.get('status_record_length', 0)
        
        content += f"""    {{
        .rid = {rid},
        .supported_subfunctions = 0x{sf_bitmask:02X}U,
        .start_option_len = {start_opt_len}U,
        .start_status_len = {start_stat_len}U,
        .stop_option_len = {stop_opt_len}U,
        .stop_status_len = {stop_stat_len}U,
        .results_option_len = {results_opt_len}U,
        .results_status_len = {results_stat_len}U,
        .callback = {callback},
        .session_mask = {session_mask},
        .security_mask = {security_mask}  // {desc}
    }},
"""
    
    content += """};

#define ROUTINE_REGISTRY_SIZE (sizeof(routine_registry) / sizeof(uds_routine_entry_t))

/* ========================================================================== */
/*                         Registry Access Functions                          */
/* ========================================================================== */

/**
 * @brief Find routine entry in registry
 */
const uds_routine_entry_t* uds_routine_find_entry(uint16_t rid)
{
    for (uint16_t i = 0; i < ROUTINE_REGISTRY_SIZE; i++) {
        if (routine_registry[i].rid == rid) {
            return &routine_registry[i];
        }
    }
    return NULL;
}

/**
 * @brief Get routine registry
 */
const uds_routine_entry_t* uds_routine_get_registry(uint16_t *count)
{
    if (count != NULL) {
        *count = ROUTINE_REGISTRY_SIZE;
    }
    return routine_registry;
}

/**
 * @brief Validate option_record length for routine
 */
bool uds_routine_validate_option_length(const uds_routine_entry_t *entry, 
                                         uint8_t sub_function, 
                                         uint16_t option_record_len)
{
    if (entry == NULL) {
        return false;
    }
    
    uint16_t expected_len = 0;
    
    switch (sub_function) {
        case UDS_ROUTINE_CONTROL_START:
            expected_len = entry->start_option_len;
            break;
        case UDS_ROUTINE_CONTROL_STOP:
            expected_len = entry->stop_option_len;
            break;
        case UDS_ROUTINE_CONTROL_REQUEST_RESULTS:
            expected_len = entry->results_option_len;
            break;
        default:
            return false;
    }
    
    // If expected_len is 0, any length is accepted (variable/optional)
    if (expected_len == 0) {
        return true;
    }
    
    // Otherwise, must match exactly
    return (option_record_len == expected_len);
}
"""
    
    return content


def generate_routine_config(config_data: Dict, output_dir: str) -> Tuple[bool, List[str]]:
    """Main generation function for routine configuration"""
    
    routines = config_data.get('routines', [])
    sessions = config_data.get('sessions', [])
    security_levels = config_data.get('security_levels', [])
    
    # Validate routines
    valid, errors = validate_routines(routines)
    if not valid:
        return False, errors
    
    try:
        # Generate header file
        header_content = generate_routine_header(routines, output_dir)
        header_path = f"{output_dir}/Routine_Gen/Routine_PBCfg.h"
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write(header_content)
        
        # Generate source file
        source_content = generate_routine_source(routines, sessions, security_levels, output_dir)
        source_path = f"{output_dir}/Routine_Gen/Routine_PBCfg.c"
        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(source_content)
        
        messages = [
            f"Generated: {header_path}",
            f"Generated: {source_path}",
            f"Total routines: {len(routines)}"
        ]
        
        return True, messages
        
    except Exception as e:
        return False, [f"Generation error: {str(e)}"]


if __name__ == '__main__':
    # Test validation
    test_routine = {
        'rid': '0xFF00',
        'routine_name': 'ROUTINE_ERASE_MEMORY',
        'callback_function': 'routine_erase_memory',
        'supported_subfunctions': ['START', 'REQUEST_RESULTS'],
        'supported_sessions': ['DCM_PROGRAMMING_SESSION'],
        'required_security_levels': [1, 2]
    }
    
    valid, msg = validate_routine_config(test_routine)
    print(f"Validation: {valid}, {msg}")
