import {
    ServerRunner,
    Backend,
    ConsoleStrategy,
  } from "microservice-framework";

  import { ChatbotServer } from "./chatbot";
  import path from "path";


  const namespace = "chatbot";
  const logStrategy = new ConsoleStrategy();
  const backend = new Backend();
  
  const chatbotServer = new ChatbotServer(backend, {
    namespace,
    logStrategy,
    serviceId: "webservice",
    port: 8082,
    staticDir: path.join(path.resolve(__dirname, "../../.."), "/public"),
    apiPrefix: "/api",
  });
  
  
  const server = new ServerRunner();
  server.registerService(chatbotServer);
  
  server.start();




