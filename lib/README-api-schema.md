# API Schema Contract System

## Overview
This system implements API Schema Contracts to prevent the "Dashboard Problem" where frontend and backend fields are inconsistent (e.g., frontend uses `model/tags/last_heartbeat` while backend uses `emoji/tasks_completed/last_active`).

## Core Components

### 1. SchemaValidator Class
- Validates API requests/responses against JSON Schema
- Generates TypeScript types from schemas
- Compares frontend vs backend schemas for consistency
- Provides detailed validation reports

### 2. Contract Definition Format
API contracts are defined in JSON Schema format with endpoint specifications:

```json
{
  "name": "agents-api",
  "version": "1.0.0", 
  "baseUrl": "/api/v1",
  "endpoints": {
    "getAgents": {
      "method": "GET",
      "path": "/agents",
      "response": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "model": {"type": "string"},
          "tags": {"type": "array", "items": {"type": "string"}},
          "last_heartbeat": {"type": "string"}
        }
      }
    }
  }
}
```

## Development Workflow

### Wave 1: Design Phase (Before Implementation)
1. **Define Schemas First**: Create JSON Schema contracts before writing any code
2. **Review & Approve**: Team reviews schemas for consistency and business requirements
3. **Generate Types**: Auto-generate TypeScript interfaces from schemas
4. **Share Contracts**: Distribute to frontend and backend teams

### Implementation Phase
1. **Frontend Implementation**: Use generated TypeScript types
2. **Backend Implementation**: Validate responses against schema
3. **Integration Testing**: Verify both sides conform to schema

### Quality Assurance
1. **Schema Consistency Check**: Run schema comparison to detect drift
2. **Automated Validation**: Integrate validation into CI/CD pipeline
3. **Documentation**: Keep API documentation in sync with schemas

## Integration with GSD Workflow

### Wave 1: Requirements & Design
- Define API contracts during requirement analysis
- Establish schema registry for all services
- Set up automated schema validation tools

### Wave 2: Development
- Integrate schema validation into development environment
- Use generated types in both frontend and backend
- Implement schema comparison in pull request checks

### Wave 3: Testing & Deployment
- Run schema consistency checks in CI/CD
- Monitor for schema drift in production
- Maintain schema version compatibility

## Benefits

1. **Prevents Field Drift**: Ensures frontend and backend stay synchronized
2. **Early Bug Detection**: Catches inconsistencies before testing phase
3. **Improved Communication**: Clear contract between frontend and backend teams
4. **Auto-Generated Types**: Reduces manual type definition errors
5. **Documentation**: Self-documenting APIs through schemas

## Usage Examples

### Validating Requests/Responses
```typescript
const validator = new SchemaValidator();
validator.registerContract(agentContract);

// Validate incoming request
const validationResult = validator.validateRequest('createAgent', requestData);

// Validate outgoing response  
const responseValidation = validator.validateResponse('getAgents', responseData);
```

### Comparing Frontend vs Backend Schemas
```typescript
const diffs = validator.compareSchemas(frontendSchema, backendSchema);
if (diffs.length > 0) {
  console.log('Schema inconsistencies found:');
  console.log(validator.formatDiffReport([{endpoint: 'comparison', diffs}]));
}
```

### Generating TypeScript Types
```typescript
const tsCode = validator.generateTypescript(schema, 'AgentType');
// Output: interface AgentType { id: string; name: string; ... }
```

## Best Practices

1. **Version Control**: Store schemas in version-controlled repository
2. **Backward Compatibility**: Ensure new schema versions maintain compatibility
3. **Regular Reviews**: Periodically review schemas for business alignment
4. **Automated Checks**: Run schema validation in CI/CD pipelines
5. **Documentation**: Keep schema documentation updated with business logic

## File Structure
```
lib/
├── api-schema-validator.ts     # Core validation logic
├── api-schema-examples/       # Example schemas
│   ├── agents.schema.json
│   └── tasks.schema.json
├── api-schema-validator.test.ts # Unit tests
└── README-api-schema.md       # This document
```

This system ensures that the "Dashboard Problem" is caught early in the development cycle, preventing costly fixes during the testing phase.