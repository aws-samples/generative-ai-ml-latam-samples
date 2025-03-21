# Use Node.js 20 as the base image
FROM arm64v8/node:20



# Set the working directory in the container
WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" \
&& unzip awscliv2.zip \
&& ./aws/install \
&& rm -rf aws awscliv2.zip

# Command to run the application
CMD ["node", "dist/microservices/chatbot/index.js"]