import requests


class Document:
    """
    A class for working with documents, including downloading and reading binary files.
    """
    
    @staticmethod
    def download_file(url: str, save_path: str = None) -> bytes:
        """
        Download a file from a URL and optionally save it to a specified path.
        
        Args:
            url (str): The URL of the file to download
            save_path (str, optional): Path where the file should be saved. Defaults to None.
            
        Returns:
            bytes: The content of the downloaded file
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception for bad status codes
            content = response.content
            
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(content)

            return response.content        
            
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")
            return b''
    
    @staticmethod
    def read_binary_file(file_path: str) -> bytes:
        """
        Read a binary file from the specified path.
        
        Args:
            file_path (str): Path to the binary file
            
        Returns:
            bytes: The content of the binary file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        try:
            with open(file_path, 'rb') as binary_file:
                content = binary_file.read()
                return content
        except FileNotFoundError:
            raise FileNotFoundError(f"Binary file not found at path: {file_path}")
        except IOError as e:
            raise IOError(f"Error reading binary file: {str(e)}")