"""
DCM Service Configuration Module
Validates and generates code for UDS service handlers
"""

import re
from typing import List, Dict, Any, Tuple


class ServiceValidator:
    """Validator for DCM service configurations"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_service_id(self, service_id: str) -> bool:
        """Validate service ID is valid hex (0x10-0xFF)"""
        if not service_id:
            self.errors.append("Service ID cannot be empty")
            return False
        
        # Check hex format
        if not re.match(r'^0x[0-9A-Fa-f]{2}$', service_id):
            self.errors.append(f"Service ID '{service_id}' must be in format 0xXX (e.g., 0x10, 0x22)")
            return False
        
        # Convert and check range
        try:
            value = int(service_id, 16)
            if value < 0x10 or value > 0xFF:
                self.errors.append(f"Service ID {service_id} must be in range 0x10-0xFF")
                return False
        except ValueError:
            self.errors.append(f"Invalid hex value: {service_id}")
            return False
        
        return True
    
    def validate_handler_name(self, handler_name: str) -> bool:
        """Validate handler function name is valid C identifier"""
        if not handler_name:
            self.errors.append("Handler function name cannot be empty")
            return False
        
        # Check C identifier format
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', handler_name):
            self.errors.append(f"Handler '{handler_name}' must be valid C identifier")
            return False
        
        # Check length
        if len(handler_name) > 64:
            self.errors.append(f"Handler name '{handler_name}' too long (max 64 chars)")
            return False
        
        return True
    
    def validate_sessions(self, sessions: List[str], available_sessions: List[str]) -> bool:
        """Validate session list"""
        if not sessions:
            self.errors.append("At least one session must be selected")
            return False
        
        # Check all sessions are valid
        for session in sessions:
            if session not in available_sessions:
                self.errors.append(f"Unknown session: {session}")
                return False
        
        return True
    
    def validate_security_levels(self, security_levels: List[int], available_levels: List[int]) -> bool:
        """Validate security level list (can be empty)"""
        # Empty is allowed (no security required)
        if not security_levels:
            return True
        
        # Check all levels are valid
        for level in security_levels:
            if level not in available_levels:
                self.errors.append(f"Unknown security level: {level}")
                return False
        
        return True
    
    def validate_service(self, service: Dict[str, Any], 
                        available_sessions: List[str],
                        available_security_levels: List[int]) -> bool:
        """Validate single service configuration"""
        self.errors.clear()
        self.warnings.clear()
        
        # Validate required fields
        if 'service_id' not in service:
            self.errors.append("Missing 'service_id' field")
            return False
        
        if 'handler_name' not in service:
            self.errors.append("Missing 'handler_name' field")
            return False
        
        if 'supported_sessions' not in service:
            self.errors.append("Missing 'supported_sessions' field")
            return False
        
        # Validate each field
        valid = True
        valid &= self.validate_service_id(service['service_id'])
        valid &= self.validate_handler_name(service['handler_name'])
        valid &= self.validate_sessions(service['supported_sessions'], available_sessions)
        
        # Security levels are optional
        if 'required_security_levels' in service:
            valid &= self.validate_security_levels(
                service['required_security_levels'], 
                available_security_levels
            )
        
        return valid
    
    def validate_services(self, services: List[Dict[str, Any]], 
                         available_sessions: List[str],
                         available_security_levels: List[int]) -> Tuple[bool, List[str], List[str]]:
        """Validate all services and check for duplicates"""
        self.errors.clear()
        self.warnings.clear()
        
        if not services:
            self.warnings.append("No services configured")
            return True, [], self.warnings
        
        # Check for duplicate service IDs
        service_ids = []
        for service in services:
            if 'service_id' in service:
                sid = service['service_id']
                if sid in service_ids:
                    self.errors.append(f"Duplicate service ID: {sid}")
                    return False, self.errors, self.warnings
                service_ids.append(sid)
        
        # Validate each service
        for i, service in enumerate(services):
            if not self.validate_service(service, available_sessions, available_security_levels):
                # Prepend service index to errors
                self.errors = [f"Service {i} ({service.get('service_id', 'unknown')}): {err}" 
                              for err in self.errors]
                return False, self.errors, self.warnings
        
        return True, [], self.warnings


class ServiceGenerator:
    """Generator for DCM service configuration code"""
    
    def __init__(self, services: List[Dict[str, Any]], 
                 session_map: Dict[str, int],
                 security_map: Dict[int, int]):
        self.services = services
        self.session_map = session_map
        self.security_map = security_map
    
    def calculate_session_mask(self, session_names: List[str]) -> int:
        """Calculate session bitmask from session names"""
        mask = 0
        for name in session_names:
            if name in self.session_map:
                mask |= self.session_map[name]
        return mask
    
    def calculate_security_mask(self, security_levels: List[int]) -> int:
        """Calculate security bitmask from level numbers"""
        mask = 0
        for level in security_levels:
            mask |= (1 << level)
        return mask
    
    def generate_header(self) -> str:
        """Generate Service_PBCfg.h"""
        header = """#ifndef SERVICE_PBCFG_H
#define SERVICE_PBCFG_H

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

/* Forward declarations */
#ifndef STD_TYPES_H
typedef uint8_t Std_ReturnType;
typedef uint8_t ErrorCode_t;
#define E_OK 0x00u
#define E_NOT_OK 0x01u
#endif

/* UDS message structure */
typedef struct {
    const uint8_t *request;     /* Request buffer (including SID) */
    uint16_t request_len;       /* Request length */
    uint8_t *response;          /* Response buffer (output) */
    uint16_t *response_len;     /* Response length (output) */
} uds_message_t;

/* Service handler function pointer type */
typedef Std_ReturnType (*uds_service_handler_t)(const uds_message_t *message, ErrorCode_t *error_code);

/* Service configuration structure */
typedef struct {
    uint8_t service_id;                 /* Service ID (SID) */
    uds_service_handler_t handler;      /* Handler function */
    uint32_t session_mask;              /* Allowed sessions bitmask */
    uint32_t security_mask;             /* Required security levels bitmask */
} dcm_service_config_t;

"""
        
        # Extern declarations for handler functions
        handler_funcs = set()
        for service in self.services:
            # Generate handler name based on service_id (e.g., 0x10 -> uds_service_0x10_handler)
            service_id = service['service_id']
            handler_name = f"uds_service_{service_id}_handler"
            handler_funcs.add(handler_name)
        
        if handler_funcs:
            header += "/* Extern handler function declarations */\n"
            for func in sorted(handler_funcs):
                header += f"extern Std_ReturnType {func}(const uds_message_t *message, ErrorCode_t *error_code);\n"
            header += "\n"
        
        # Config table declaration
        service_count = len(self.services)
        header += f"/* Service configuration table */\n"
        header += f"#define DCM_SERVICE_COUNT {service_count}u\n"
        header += f"extern const dcm_service_config_t dcm_service_config_table[DCM_SERVICE_COUNT];\n\n"
        
        header += "#endif /* SERVICE_PBCFG_H */\n"
        return header
    
    def generate_source(self) -> str:
        """Generate Service_PBCfg.c"""
        source = """#include "Service_PBCfg.h"

/* Service configuration table */
const dcm_service_config_t dcm_service_config_table[DCM_SERVICE_COUNT] = {
"""
        
        for i, service in enumerate(self.services):
            service_id = service['service_id']
            # Generate handler name based on service_id (e.g., 0x10 -> uds_service_0x10_handler)
            handler = f"uds_service_{service_id}_handler"
            service_name = service.get('service_name', service_id)
            sessions = service['supported_sessions']
            security_levels = service.get('required_security_levels', [])
            
            # Calculate masks
            session_mask = self.calculate_session_mask(sessions)
            security_mask = self.calculate_security_mask(security_levels)
            
            # Format session names for comment
            session_comment = ', '.join(sessions) if sessions else ''
            
            # Format security levels for comment
            if security_levels:
                security_comment = ', '.join([f"Level {l}" for l in security_levels])
            else:
                security_comment = ''
            
            source += f"    /* Service {service_id} - {service_name} */\n"
            source += f"    {{\n"
            source += f"        .service_id = {service_id},\n"
            source += f"        .handler = {handler},\n"
            source += f"        .session_mask = {session_mask}u,  /* {session_comment} */\n"
            source += f"        .security_mask = {security_mask}u  /* {security_comment} */\n"
            source += f"    }}"
            
            if i < len(self.services) - 1:
                source += ","
            source += "\n"
        
        source += "};\n"
        return source
    
    def generate_cmake(self) -> str:
        """Generate CMakeLists.txt snippet for Service_Gen"""
        cmake = """# Service configuration files
file(GLOB SERVICE_GEN_SOURCES "Service_Gen/*.c")
if(SERVICE_GEN_SOURCES)
    target_sources(${PROJECT_NAME} PRIVATE ${SERVICE_GEN_SOURCES})
    target_include_directories(${PROJECT_NAME} PRIVATE Service_Gen)
endif()
"""
        return cmake


def validate_services(services, sessions, security_levels):
    """Export function for validation"""
    validator = ServiceValidator()
    
    # Extract available session names
    available_sessions = [s['session_name'] for s in sessions]
    
    # Extract available security level numbers
    available_security = [s['security_level'] for s in security_levels]
    
    return validator.validate_services(services, available_sessions, available_security)


def generate_service_code(services, sessions, security_levels, output_dir):
    """Generate service configuration code"""
    import os
    
    # Create session map (name -> bitmask value)
    session_map = {}
    for session in sessions:
        name = session['session_name']
        value = int(session['session_value'], 16)
        session_map[name] = (1 << value)
    
    # Create security map (level -> bitmask value)
    security_map = {}
    for level_config in security_levels:
        level = level_config['security_level']
        security_map[level] = (1 << level)
    
    # Generate code
    generator = ServiceGenerator(services, session_map, security_map)
    header_content = generator.generate_header()
    source_content = generator.generate_source()
    
    # Create output directory
    service_gen_dir = os.path.join(output_dir, 'Service_Gen')
    os.makedirs(service_gen_dir, exist_ok=True)
    
    # Write files
    header_path = os.path.join(service_gen_dir, 'Service_PBCfg.h')
    source_path = os.path.join(service_gen_dir, 'Service_PBCfg.c')
    
    with open(header_path, 'w') as f:
        f.write(header_content)
    
    with open(source_path, 'w') as f:
        f.write(source_content)
    
    return [header_path, source_path]
