#!/bin/bash

# MIT No Attribution
#
# Copyright 2025 Amazon Web Services
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Usage function
usage() {
    echo "Usage: $0 <mode> [options]"
    echo ""
    echo "Modes:"
    echo "  create-all                    Deploy all agents (create new - will fail if agents already exist)"
    echo "  update <agent>                Update a specific agent (agent ID will be auto-discovered)"
    echo ""
    echo "Agents for update mode:"
    echo "  lawyer                        Update lawyer agent"
    echo "  auditor                       Update auditor agent"
    echo "  writer                        Update writer agent"
    echo ""
    echo "Examples:"
    echo "  $0 create-all"
    echo "  $0 update lawyer"
    echo "  $0 update auditor"
    echo "  $0 update writer"
    exit 1
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    usage
fi

MODE="$1"

case "$MODE" in
    "create-all")
        DEPLOY_MODE="create"
        echo "Selected: Deploy all agents (create mode)"
        ;;
    "update")
        if [ $# -ne 2 ]; then
            echo "Error: Update mode requires agent type"
            usage
        fi
        DEPLOY_MODE="update"
        AGENT_TYPE="$2"
        
        case "$AGENT_TYPE" in
            "lawyer"|"auditor"|"writer")
                echo "Selected: Update $AGENT_TYPE agent (agent ID will be auto-discovered)"
                ;;
            *)
                echo "Error: Invalid agent type '$AGENT_TYPE'. Must be 'lawyer', 'auditor', or 'writer'"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "Error: Invalid mode '$MODE'"
        usage
        ;;
esac

echo "Copying user analysis mapping to lawyer agent"
cp ../shared/analysis_lenses/user_analysis_mapping.py ./lawyer_agent/query_categorization_tool/user_analysis_mapping.py 

ECR_REPO_PREFIX="bedrock-agentcore/regulatory-compliance-analysis"
AWS_COMPLIANCE_ANALYSIS_AGENTS_DEPLOY_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

#Login into public ECR
echo "Logging into public ECR"
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws

# Function to get agent configuration based on agent type
get_agent_config() {
    local agent_type="$1"
    local config_type="$2"  # runtime_name, repo_name, or directory
    
    case "$agent_type" in
        "lawyer")
            case "$config_type" in
                "runtime_name") echo "compliance_analysis_lawyer_agent" ;;
                "repo_name") echo "lawyer-agent" ;;
                "directory") echo "lawyer_agent" ;;
                *) echo "Error: Invalid config type '$config_type'" >&2; exit 1 ;;
            esac
            ;;
        "auditor")
            case "$config_type" in
                "runtime_name") echo "compliance_analysis_auditor_agent" ;;
                "repo_name") echo "auditor_agent" ;;
                "directory") echo "auditor_agent" ;;
                *) echo "Error: Invalid config type '$config_type'" >&2; exit 1 ;;
            esac
            ;;
        "writer")
            case "$config_type" in
                "runtime_name") echo "compliance_analysis_writer_agent" ;;
                "repo_name") echo "writer_agent" ;;
                "directory") echo "writer_agent" ;;
                *) echo "Error: Invalid config type '$config_type'" >&2; exit 1 ;;
            esac
            ;;
        *)
            echo "Error: Invalid agent type '$agent_type'" >&2
            exit 1
            ;;
    esac
}

# Function to find agent runtime ID by agent type
find_agent_runtime_id() {
    local agent_type="$1"
    local runtime_name=$(get_agent_config "$agent_type" "runtime_name")
    
    echo "Looking for existing agent runtime: $runtime_name" >&2
    
    # Extract the agent runtime ID for the matching agent name
    local agent_id=$(echo "$EXISTING_AGENTS_JSON" | jq -r --arg name "$runtime_name" '.agentRuntimes[]? | select(.agentRuntimeName == $name) | .agentRuntimeId' 2>/dev/null)
    
    if [ -z "$agent_id" ] || [ "$agent_id" = "null" ]; then
        echo "Error: Agent runtime '$runtime_name' not found. Available agents:" >&2
        echo "$EXISTING_AGENTS_LIST" >&2
        echo "" >&2
        echo "Please ensure the agent exists before trying to update it, or use 'create-all' mode to create new agents." >&2
        exit 1
    fi
    
    echo "Found agent runtime ID: $agent_id" >&2
    echo "$agent_id"
}

# Function to load environment variables from .env file
load_env_vars() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        echo "Loading environment variables from $env_file"
        # Read .env file and create map format for AWS CLI (key1=value1,key2=value2)
        ENV_VARS_MAP=""
        first=true
        while IFS='=' read -r key value || [ -n "$key" ]; do
            # Skip empty lines and comments
            if [ -n "$key" ] && ! echo "$key" | grep -q '^[[:space:]]*#'; then
                # Remove leading/trailing whitespace
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs)
                
                if [ "$first" = true ]; then
                    first=false
                else
                    ENV_VARS_MAP+=","
                fi
                ENV_VARS_MAP+="$key=$value"
            fi
        done < "$env_file"
        echo "Environment variables map: $ENV_VARS_MAP"
    else
        echo "Warning: .env file not found at $env_file"
        ENV_VARS_MAP=""
    fi
}

# Function to deploy or update an agent
deploy_agent() {
    local agent_name="$1"
    local agent_runtime_name="$2"
    local repo_name="$3"
    local directory="$4"
    local agent_id="$5"  # Only used for update mode

    echo $agent_name
    echo $agent_runtime_name
    echo $repo_name
    echo $directory
    
    echo "################## PROCESSING $(echo "$agent_name" | tr '[:lower:]' '[:upper:]') AGENT ##################"
    
    # Navigate to agent directory
    if [ "$directory" != "." ]; then
        cd "$directory"
    fi
    
    # Load environment variables from .env file
    load_env_vars ".env"
    
    # Debug: Print the exact repository name being used
    echo "Debug: ECR_REPO_PREFIX='$ECR_REPO_PREFIX'"
    echo "Debug: repo_name='$repo_name'"
    echo "Debug: Full repository name='$ECR_REPO_PREFIX/$repo_name'"
    
    # Check if repository exists, create only if it doesn't
    REPO_EXISTS=$(aws ecr describe-repositories --repository-names "$ECR_REPO_PREFIX/$repo_name" --region "$AWS_DEFAULT_REGION" 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "Repository does not exist. Creating repository: $ECR_REPO_PREFIX/$repo_name"
        if ! aws ecr create-repository --repository-name "$ECR_REPO_PREFIX/$repo_name" --region "$AWS_DEFAULT_REGION" --no-paginate; then
            echo "Error: Failed to create ECR repository '$ECR_REPO_PREFIX/$repo_name'"
            exit 1
        fi
        echo "Repository created successfully: $ECR_REPO_PREFIX/$repo_name"
    else
        echo "Repository already exists: $ECR_REPO_PREFIX/$repo_name"
    fi
    
    # Build and push Docker image
    CONTAINER_URI="${AWS_COMPLIANCE_ANALYSIS_AGENTS_DEPLOY_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPO_PREFIX}/${repo_name}:latest"
    echo "Building and pushing Docker image..."
    echo "Debug: Container URI='$CONTAINER_URI'"
    
    if ! docker buildx build --platform linux/arm64 -t "$CONTAINER_URI" --push .; then
        echo "Error: Docker build and push failed for $agent_name agent"
        echo "Container URI: $CONTAINER_URI"
        exit 1
    fi
    echo "Docker image successfully built and pushed to: $CONTAINER_URI"
    
    # Check if AGENT_CORE_ROLE_ARN is set
    if [ -z "$AGENT_CORE_ROLE_ARN" ]; then
        echo "Error: AGENT_CORE_ROLE_ARN environment variable is not set"
        exit 1
    fi
    
    echo "Using Agent Role ARN: $AGENT_CORE_ROLE_ARN"
    echo "Container URI: ${AWS_COMPLIANCE_ANALYSIS_AGENTS_DEPLOY_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPO_PREFIX}/${repo_name}:latest"
    
    # Deploy or update agent based on mode
    if [ "$DEPLOY_MODE" = "create" ]; then
        # Check if agent runtime already exists - should NOT exist for create mode
        echo "Checking if agent runtime exists: $agent_runtime_name"
        if echo "$EXISTING_AGENTS_LIST" | grep -q "$agent_runtime_name"; then
            echo "Error: Agent runtime '$agent_runtime_name' already exists. Use update mode instead."
            exit 1
        fi
        
        echo "Creating new agent runtime..."
        if [ -n "$ENV_VARS_MAP" ]; then
            AGENT_RESPONSE=$(aws bedrock-agentcore-control create-agent-runtime \
                --agent-runtime-name "$agent_runtime_name" \
                --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${AWS_COMPLIANCE_ANALYSIS_AGENTS_DEPLOY_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPO_PREFIX}/${repo_name}:latest\"}}" \
                --network-configuration '{"networkMode":"PUBLIC"}' \
                --role-arn "$AGENT_CORE_ROLE_ARN" \
                --environment-variables "$ENV_VARS_MAP" \
                --region "$AWS_DEFAULT_REGION" 2>&1 \
                --no-paginate)
        else
            AGENT_RESPONSE=$(aws bedrock-agentcore-control create-agent-runtime \
                --agent-runtime-name "$agent_runtime_name" \
                --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${AWS_COMPLIANCE_ANALYSIS_AGENTS_DEPLOY_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPO_PREFIX}/${repo_name}:latest\"}}" \
                --network-configuration '{"networkMode":"PUBLIC"}' \
                --role-arn "$AGENT_CORE_ROLE_ARN" \
                --region "$AWS_DEFAULT_REGION" 2>&1 \
                --no-paginate)
        fi
        
        # Check if the creation was successful
        if [ $? -ne 0 ]; then
            echo "Error creating agent runtime:"
            echo "$AGENT_RESPONSE"
            exit 1
        fi
        
        echo "Agent creation response:"
        echo "$AGENT_RESPONSE"
        
    elif [ "$DEPLOY_MODE" = "update" ]; then
        echo "Updating existing agent runtime with ID: $agent_id"
        
        if [ -n "$ENV_VARS_MAP" ]; then
            AGENT_RESPONSE=$(aws bedrock-agentcore-control update-agent-runtime \
                --agent-runtime-id "$agent_id" \
                --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${AWS_COMPLIANCE_ANALYSIS_AGENTS_DEPLOY_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPO_PREFIX}/${repo_name}:latest\"}}" \
                --network-configuration '{"networkMode":"PUBLIC"}' \
                --role-arn "$AGENT_CORE_ROLE_ARN" \
                --environment-variables "$ENV_VARS_MAP" \
                --region "$AWS_DEFAULT_REGION" 2>&1)
        else
            AGENT_RESPONSE=$(aws bedrock-agentcore-control update-agent-runtime \
                --agent-runtime-id "$agent_id" \
                --agent-runtime-artifact "{\"containerConfiguration\":{\"containerUri\":\"${AWS_COMPLIANCE_ANALYSIS_AGENTS_DEPLOY_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPO_PREFIX}/${repo_name}:latest\"}}" \
                --network-configuration '{"networkMode":"PUBLIC"}' \
                --role-arn "$AGENT_CORE_ROLE_ARN" \
                --region "$AWS_DEFAULT_REGION" 2>&1)
        fi
        
        # Check if the update was successful
        if [ $? -ne 0 ]; then
            echo "Error updating agent runtime:"
            echo "$AGENT_RESPONSE"
            exit 1
        fi
        
        echo "Agent update response:"
        echo "$AGENT_RESPONSE"
    fi
    
    # Extract ARN from response
    AGENT_RUNTIME_ARN=$(echo "$AGENT_RESPONSE" | jq -r '.agentRuntimeArn')
    echo "Extracted $(echo "$agent_name" | sed 's/./\U&/') Agent Runtime ARN: $AGENT_RUNTIME_ARN"
    
    if [ "$AGENT_RUNTIME_ARN" = "null" ] || [ -z "$AGENT_RUNTIME_ARN" ]; then
        echo "Error: Failed to extract agent runtime ARN from response"
        echo "Full response: $AGENT_RESPONSE"
        exit 1
    fi
    
    # Set the appropriate variable based on agent type
    case "$agent_name" in
        "lawyer")
            LAWYER_AGENT_RUNTIME_ARN="$AGENT_RUNTIME_ARN"
            ;;
        "auditor")
            AUDITOR_AGENT_RUNTIME_ARN="$AGENT_RUNTIME_ARN"
            ;;
        "writer")
            WRITER_AGENT_RUNTIME_ARN="$AGENT_RUNTIME_ARN"
            ;;
    esac
}

# Get list of existing agent runtimes at the beginning
echo "Fetching list of existing agent runtimes..."
EXISTING_AGENTS_JSON=$(aws bedrock-agentcore-control list-agent-runtimes --region "$AWS_DEFAULT_REGION" --output json 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "Warning: Could not fetch existing agent runtimes list. Proceeding with create operation."
    EXISTING_AGENTS_JSON="{\"agentRuntimes\":[]}"
fi

# Extract agent names and IDs for easier lookup
EXISTING_AGENTS_LIST=$(echo "$EXISTING_AGENTS_JSON" | jq -r '.agentRuntimes[]? | .agentRuntimeName' 2>/dev/null || echo "")

echo "Existing agents: ${EXISTING_AGENTS_LIST}"

echo "Logging into private ECR"
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_COMPLIANCE_ANALYSIS_AGENTS_DEPLOY_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com


######################### AGENT DEPLOYMENT #########################

# Deploy agents based on mode
if [ "$DEPLOY_MODE" = "create" ]; then
    # Deploy all agents
    for agent_type in "lawyer" "auditor" "writer"; do
        runtime_name=$(get_agent_config "$agent_type" "runtime_name")
        repo_name=$(get_agent_config "$agent_type" "repo_name")
        directory=$(get_agent_config "$agent_type" "directory")
        
        deploy_agent "$agent_type" "$runtime_name" "$repo_name" "$directory"
        cd ..
    done
elif [ "$DEPLOY_MODE" = "update" ]; then
    # Find the agent runtime ID automatically
    AGENT_ID=$(find_agent_runtime_id "$AGENT_TYPE")
    
    # Deploy only the specified agent
    runtime_name=$(get_agent_config "$AGENT_TYPE" "runtime_name")
    repo_name=$(get_agent_config "$AGENT_TYPE" "repo_name")
    directory=$(get_agent_config "$AGENT_TYPE" "directory")
    
    echo "Updating $AGENT_TYPE agent with auto-discovered ID: $AGENT_ID"
    deploy_agent "$AGENT_TYPE" "$runtime_name" "$repo_name" "$directory" "$AGENT_ID"
    cd ..
fi

################## DEPLOYMENT COMPLETE ##################

echo "################## DEPLOYMENT COMPLETE ##################"

# Export the variables for use in other scripts or processes
if [ "$DEPLOY_MODE" = "create" ]; then
    export LAWYER_AGENT_RUNTIME_ARN
    export AUDITOR_AGENT_RUNTIME_ARN  
    export WRITER_AGENT_RUNTIME_ARN

    echo "Final Agent Runtime ARNs:"
    echo "Lawyer Agent Runtime ARN: $LAWYER_AGENT_RUNTIME_ARN"
    echo "Auditor Agent Runtime ARN: $AUDITOR_AGENT_RUNTIME_ARN"
    echo "Writer Agent Runtime ARN: $WRITER_AGENT_RUNTIME_ARN"

    # Also save to a file for persistence
    cat > agent_arns.env << EOF
LAWYER_AGENT_RUNTIME_ARN=$LAWYER_AGENT_RUNTIME_ARN
AUDITOR_AGENT_RUNTIME_ARN=$AUDITOR_AGENT_RUNTIME_ARN
WRITER_AGENT_RUNTIME_ARN=$WRITER_AGENT_RUNTIME_ARN
EOF

    echo "Agent ARNs saved to agent_arns.env file"
elif [ "$DEPLOY_MODE" = "update" ]; then
    case "$AGENT_TYPE" in
        "lawyer")
            export LAWYER_AGENT_RUNTIME_ARN
            echo "Updated Lawyer Agent Runtime ARN: $LAWYER_AGENT_RUNTIME_ARN"
            ;;
        "auditor")
            export AUDITOR_AGENT_RUNTIME_ARN
            echo "Updated Auditor Agent Runtime ARN: $AUDITOR_AGENT_RUNTIME_ARN"
            ;;
        "writer")
            export WRITER_AGENT_RUNTIME_ARN
            echo "Updated Writer Agent Runtime ARN: $WRITER_AGENT_RUNTIME_ARN"
            ;;
    esac
    echo "Agent update completed successfully"
fi