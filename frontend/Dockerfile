FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Development command (override in docker-compose for production)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

