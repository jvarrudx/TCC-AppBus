FROM node:20-alpine

WORKDIR /app

# Install dependencies first (leverage Docker caching)
COPY package.json package-lock.json* /app/
RUN npm install

# Copy the rest of the files
COPY . /app/

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
