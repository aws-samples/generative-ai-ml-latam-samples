# MIT No Attribution
#
# Copyright 2024 Amazon Web Services
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

from pydantic import BaseModel, Field
from typing import List

class CompraProducto(BaseModel):
  """Informacion acerca de cada una de las compras anotadas en el recibo"""
  product_name: str = Field(description="El nombre del producto adquirido")
  number_items: int = Field(1, description="El numero de articulos adquiridos del mismo producto")
  unit_cost: float = Field(description="El costo unitario del producto")
  unit: str = Field("", description="La unidad de medida para el producto")
  total_cost: float = Field(description="El costo total de todos los productos adquiridos")

class InformacionRecibo(BaseModel):
    """Informacion general acerca de la sociedad o compañia"""
    vendor_name: str = Field(description="El nombre del vendedor")
    expedition_date: str = Field(description="La fecha de expedicion del recibo")
    products: List[CompraProducto] = Field(description="La lista de productos adquiridos en esta compra")
    total_cost: float = Field(description="El monto total de la compra")