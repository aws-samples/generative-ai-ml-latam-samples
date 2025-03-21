
import {
    WebServer,
    HttpRequest,
    HttpResponse,
    WebServerConfig,
    RequestHandler,
    IBackEnd
  } from "microservice-framework";
  import { AntrhopicConvers,  } from "./AnthropicConverse";

import fs from 'fs';
import path from 'path';
import util from "util";


// Assume the image is stored in an 'images' folder in your project
const imageDirectory = "/Users/schauflc/Documents/wardrobeai/packages/backend/public/pictures"


  const converseStream = new AntrhopicConvers();

  function insertStringAtIndex(input1: string[], input2: string, input3: string[]): string[] {
    if (input1.includes(input2)) {
      const output = [...input3];
      // Find position of input2 in input1 (0-based index)
      const positionInInput1 = input1.indexOf(input2);
      
      // Use same position for insertion in output
      // If position is beyond output length, append to end
      const insertPosition = Math.min(positionInInput1, output.length);
      
      output.splice(insertPosition, 0, input2);
      return output;
    } else {
      return input3;
    }
  }

  function insertShoppingImage(input1: string[], input2: string, input3: string[]): string[] {
    // Create a copy of input1 to work with
    const result = [...input1];
    
    // Find the position of input2 in input1
    const position = input1.indexOf(input2);
    
    // If the image exists in input1, replace it with the first image from input3
    if (position !== -1) {
        result[position] = input3[0];
    }
    
    return result;
}
  
  
  export class ChatbotServer extends WebServer {
    private messageHistory: any;
    private previousImageIDs: string[];
    constructor(backend: IBackEnd, config: WebServerConfig) {
      super(backend, config);
      this.messageHistory = []
      this.previousImageIDs= []

    }

    @RequestHandler<HttpRequest>("GET:/startchat")
    public async startChatHandler(request: HttpRequest): Promise<HttpResponse> {
        const instructionsInput = 

        `
You are an expert AI fashion stylist with deep knowledge of current trends, style combinations, and personalized shopping experiences. Your task is to analyze clothing images and provide tailored recommendations while maintaining a conversation history.

<context>
You have access to a collection of clothing images, each identified with a unique Image ID (img_X). You will interact with users to understand their style preferences and make recommendations based on their choices and feedback.
</context>

<recomendation_rules>
1. Present recommendations in sets of 4 items
2. Track user preferences through two types of responses:
   - BestItem: img_X (where X is the image ID) The item the user like the most out of the 4 options, but isn't necessarily interested in purchasing it.
   - ShoppingCart: img_Y (where Y is the image ID) This means the user is interested in purchasing this item. Use it as a strong indicator of the user's taste,

</recomendation_rules>

<output>
1. If the response is BestItem: img_X:  Recomend 3 new recomended pieces.
2. If the response is ShoppingCart: Recomend 1 new piece. Remove img_Y from selection pool
3. Do not recomend images that were not given as imput. If you dont have any images left, let it know at the coments.

<example1>

Assistant: 

{
    "imageIDs": [ 'img_A', 'img_B', 'img_C', 'img_D' ],
    "comments": "...."
}

User: BestItem:img_B

Assistant: 
{
    "imageIDs": [ 'img_F', 'img_G', 'img_H' ],
    "comments": "...."
}

</example1>

<example2>

Assistant: 

{
    "imageIDs": [ 'img_A', 'img_B', 'img_C', 'img_D' ],
    "comments": "...."
}

User: ShoppingCart:img_B

Assistant: 
{
    "imageIDs": [ 'img_G' ],
    "comments": "...."
}

</example2>


</output>



<output_format>
Always respond in this JSON structure:
{
    "imageIDs": ["img_1", "img_2", "img_3"],
    "comments": "Style insights and recommendations"
}
</output_format>

<comments>

In the "comments" section be concise and precise in your comments, provide valuable styling insights such as:
   - Patterns in the user's style preferences
   - Suggestions for versatile combinations
   - Observations about color preferences, style themes, or fashion trends
   - Relevant styling advice or observations
   - If you don't have particularly insightful comments, it's acceptable to leave the "comments" field empty or with a minimal response.

</comments> 


<termination>
End the conversation when user says "finish"
</termination>


IMPORTANT: Your response must contain only the specified JSON format and nothing else.
`
        
        ;
        

        
        
        const contentBlocks = [];
        // Read all jpeg files from the directory
        const files = fs.readdirSync(imageDirectory).filter(file => file.endsWith('.jpeg'));
        // Add each image to the content blocks
        for (const file of files) {
            const imageId = `${file}`;
            const imagePath = path.join(imageDirectory, file);
            const imageBuffer = fs.readFileSync(imagePath);
            const base64Image = imageBuffer.toString('base64');

            contentBlocks.push({
                type: "text",
                text: "<item>"
            });
            
                // Add image ID
            contentBlocks.push({
            type: "text",
            text: `<image_id>${imageId}</image_id>`
            });
      
            contentBlocks.push({
                type: "image",
                source: {
                type: "base64",
                media_type: "image/jpeg",
                data: base64Image,
                }
            });

                // Add item closing tag
            contentBlocks.push({
                type: "text",
                text: "</item>"
            });
        }


        // Add the text prompt after all images
        contentBlocks.push({
            type: "text", text: instructionsInput
        });
        this.messageHistory= [({role: "user", "content": contentBlocks})]

        const modelResponse :any = await converseStream.sendContent([ {role: "user", "content": contentBlocks}]);
        const responseText = modelResponse.content[0].text

        try {
            const parsedResponse = JSON.parse(responseText);
            console.log(parsedResponse);
            this.previousImageIDs= parsedResponse.imageIDs

            this.messageHistory.push({role: "assistant", content: modelResponse.content});
            return {
                statusCode: 200,
                headers: { "Content-Type": "application/json" },
                body: { 
                    message: "Chat have Started",
                    response: parsedResponse
                  },
            };
        } catch (error: any) {
            return {
                statusCode: 500,
                headers: { "Content-Type": "application/json" },
                body: {error: error.message},
            };   
        }
    }

    @RequestHandler<HttpRequest>("POST:/bestItemHandler")
    public async bestItemHandler(request: HttpRequest): Promise<HttpResponse> {
        const ImageID = request.body.body; //{ "bestItem": ImageID}  or {"shoppingCart": ImageID}

        

        try {

    
        
            this.messageHistory.push({role: "user", "content": [ {
                type: "text", text: `bestItem:${ImageID.body}`
            }  ]});
    
            const modelResponse :any = await converseStream.sendContent(this.messageHistory);
            const responseText = modelResponse.content[0].text
    
    
    

            var parsedResponse = JSON.parse(responseText);
            const newimageIDs =insertStringAtIndex(this.previousImageIDs,ImageID.body,parsedResponse.imageIDs)
            console.log(this.previousImageIDs, ImageID.body, parsedResponse.imageIDs,newimageIDs)

            this.previousImageIDs = newimageIDs
            parsedResponse.imageIDs =newimageIDs
            

            console.log(parsedResponse);

            this.messageHistory.push({role: "assistant", content: modelResponse.content});
            return {
                statusCode: 200,
                headers: { "Content-Type": "application/json" },
                body: { 
                    message: "Chat have Started",
                    response: parsedResponse
                  },
            };
        } catch (error: any) {
            return {
                statusCode: 500,
                headers: { "Content-Type": "application/json" },
                body: {error: error.message},
            };   
        }
    }


    @RequestHandler<HttpRequest>("POST:/chatResponseHandler")
    public async chatResponseHandler(request: HttpRequest): Promise<HttpResponse> {
        const ImageID = request.body.body; //{ "bestItem": ImageID}  or {"shoppingCart": ImageID}

        this.messageHistory.push({role: "user", "content": [ {
            type: "text", text:  `shoppingCart:${ImageID}`
        }  ]});


        const modelResponse :any = await converseStream.sendContent(this.messageHistory);
        const responseText = modelResponse.content[0].text
        

        try {
            const parsedResponse = JSON.parse(responseText);

            const newimageIDs =insertShoppingImage(this.previousImageIDs,ImageID.body,parsedResponse.imageIDs)
            console.log(this.previousImageIDs, ImageID.body, parsedResponse.imageIDs,newimageIDs)

            this.previousImageIDs = newimageIDs
            parsedResponse.imageIDs =newimageIDs


            console.log(parsedResponse);
            this.messageHistory.push({role: "assistant", content: modelResponse.content});
            return {
                statusCode: 200,
                headers: { "Content-Type": "application/json" },
                body: { 
                    message: "Chat have Started",
                    response: parsedResponse
                  },
            };
        } catch (error: any) {
            return {
                statusCode: 500,
                headers: { "Content-Type": "application/json" },
                body: {error: error.message},
            };   
        }
        }
  }
