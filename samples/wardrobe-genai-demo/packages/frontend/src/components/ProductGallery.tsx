import { useState, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShoppingCart, Heart, Loader2, Sparkles } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";

const funnyMessages = [
  "🧦 Doing the fashion dance...",
  "🕶 Making sure you look cooler than cool...",
  "👚 Teaching AI to be a fashionista...",
  "🎽 Asking the fashion gods for guidance...",
  "👗 Raiding the digital closet...",
  "🧥 Playing dress-up with the algorithms...",
  "👔 Threading the digital needle...",
  "👕 Finding your next favorite outfit..."
];

interface ApiResponse {
  response: {
    imageIDs: string[];
    comments: string;
    selection_logic: string;
  }
}

interface CartItem {
  imageId: string;
  addedAt: Date;
}

const ProductGallery = () => {
  const [products, setProducts] = useState<string[]>([]);
  const [comments, setComments] = useState<string>('');
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [currentMessage, setCurrentMessage] = useState(0);
  const { toast } = useToast();


   // Add this effect to cycle through messages during loading
   useEffect(() => {
    if (isLoading) {
      const timer = setInterval(() => {
        setCurrentMessage((prev) => (prev + 1) % funnyMessages.length);
      }, 2000);
      return () => clearInterval(timer);
    }
  }, [isLoading]);

  useEffect(() => {
    if (!isInitialized) {
      initializeGallery();
      setIsInitialized(true);
    }
  }, [isInitialized]);

  const initializeGallery = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8082/api/startchat');
      const data: ApiResponse = await response.json();
      setProducts(data.response.imageIDs);
      setComments(data.response.comments);
    } catch (error) {
      console.error(error)
      toast({
        title: "Error",
        description: "Failed to load products",
        variant: "destructive",
      });
    }
    setIsLoading(false);
  };

  const handleBestItem = async (imageId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8082/api/bestItemHandler', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body: imageId })
      });
      const data: ApiResponse = await response.json();
      setProducts(data.response.imageIDs);
      setComments(data.response.comments);
    } catch (error) {
      console.error(error)
      toast({
        title: "Error",
        description: "Failed to update selection",
        variant: "destructive",
      });
    }
    setIsLoading(false);
  };

  const handleAddToCart = async (imageId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8082/api/chatResponseHandler', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body: imageId })
      });
      const data: ApiResponse = await response.json();
      setProducts(data.response.imageIDs);
      setComments(data.response.comments);
      setCartItems(prev => [...prev, { imageId, addedAt: new Date() }]);
      toast({
        title: "Success",
        description: "Added to cart",
      });
    } catch (error) {
      console.error(error)
      toast({
        title: "Error",
        description: "Failed to add to cart",
        variant: "destructive",
      });
    }
    setIsLoading(false);
  };

  const removeFromCart = (imageId: string) => {
    setCartItems(prev => prev.filter(item => item.imageId !== imageId));
    toast({
      title: "Success",
      description: "Removed from cart",
    });
  };

  return (
    <div className="container mx-auto px-8 py-12 max-w-7xl">
      <div className="mb-8 text-left">
        <h1 className="text-3xl font-bold tracking-tight">Outfit Recommendations</h1>
        <p className="text-lg text-muted-foreground mt-2">
          Find your perfect style match
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="md:col-span-3">
          {isLoading ? (
            <Card className="p-6 mb-6">
              <div className="flex flex-col items-center justify-center gap-4 py-8 bg-gradient-to-r from-stone-50 to-warm-gray-50 rounded-xl">
                <div className="relative">
                  <Loader2 className="h-12 w-12 text-primary animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl">👕</span>
                  </div>
                </div>
                <p className="text-lg font-medium">{funnyMessages[currentMessage]}</p>
                <div className="flex gap-2">
                  <span className="animate-bounce delay-100">💃</span>
                  <span className="animate-bounce delay-200">🕺</span>
                  <span className="animate-bounce delay-300">💃</span>
                </div>

                 {/* Comments integrated here */}
               {comments && (
                  <div className="mt-6 pt-6 border-t">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                        💭
                      </div>
                      <h4 className="font-medium">Style Assistant Says:</h4>
                    </div>
                    <p className="text-muted-foreground pl-10">{comments}</p>
                  </div>
                )}
              </div>
            </Card>
          ) : (
            <Card className="p-6 mb-6">
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="bg-gradient-to-r from-pink-200 to-rose-200 p-2 rounded-full">
                    <span className="text-xl">✨</span>
                  </div>
                  <h3 className="font-bold text-xl">Fashion Game Time!</h3>
                </div>
                
                <p className="text-muted-foreground">
                  Let's play a little style game! Here's how:
                </p>
  
                <div className="grid gap-3">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                      🎯
                    </div>
                    <p>
                      <span className="font-medium text-foreground">Select the one you like the most! even if you don't love it</span>
                    </p>
                  </div>
  
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                      🛍️
                    </div>
                    <p>
                      <span className="font-medium text-foreground">"This speaks to my soul!" Add your favorites to the Must Have</span>
                    </p>
                  </div>
                </div>
  
                <p className="text-sm italic text-muted-foreground mt-2 pl-10">
                  Don't think too hard - let your fashion instincts guide you! ✌️
                </p>
  
                {/* Comments integrated here */}
                {comments && (
                  <div className="mt-6 pt-6 border-t">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                        💭
                      </div>
                      <h4 className="font-medium">Style Assistant Says:</h4>
                    </div>
                    <p className="text-muted-foreground pl-10">{comments}</p>
                  </div>
                )}
              </div>
            </Card>
          )}
            
            <div className="grid grid-rows-2 grid-cols-1 sm:grid-cols-2 gap-4 auto-rows-max">
              {products.map((imageId) => (
                <Card key={imageId} className="cursor-pointer">
                  <CardContent className="p-4">
                    <img
                      src={`/pictures/${imageId}.jpeg`}
                      alt={`Product ${imageId}`}
                      className="w-full h-64 object-contain mb-4"
                      onClick={() => !isLoading && handleBestItem(imageId)}
                    />
                    <div className="flex justify-end mt-2">
                        <Button 
                          className="bg-rose-10 hover:bg-rose-50 text-black-50 hover:text-black-200 transition-colors rounded-full px-6"
                          disabled={isLoading || cartItems.some(item => item.imageId === imageId)}
                          onClick={() => handleAddToCart(imageId)}
                        >
                          {isLoading ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <Sparkles className="mr-2 h-4 w-4" />
                          )}
                          {cartItems.some(item => item.imageId === imageId) ? "Added!" : "Must Have"}
                        </Button>
                      </div>
                  </CardContent>
                </Card>
              ))}
            </div>
        </div>
  
        <div className="md:col-span-1">
          <Card className="sticky top-4">
            <CardContent className="p-4">
              <h2 className="text-lg font-semibold mb-4">Must Haves ({cartItems.length})</h2>
              {cartItems.length === 0 ? (
                <p className="text-slate-500">😴</p>
              ) : (
                <div className="space-y-4">
                  {cartItems.map((item) => (
                    <div key={item.imageId} className="flex items-center gap-2">
                      <img
                        src={`/pictures/${item.imageId}.jpeg`}
                        alt={`Product ${item.imageId}`}
                        className="w-16 h-16 object-cover rounded"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-auto text-red-500"
                        onClick={() => removeFromCart(item.imageId)}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );

};

export default ProductGallery;