import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import ProductGallery from './components/ProductGallery'
import { Toaster } from "@/components/ui/toaster"

const router = createBrowserRouter([
  {
    path: "/",
    element: <ProductGallery />,
  }
])

function App() {
  return (
    <>
      <RouterProvider router={router} />
      <Toaster />
    </>
  )
}

export default App