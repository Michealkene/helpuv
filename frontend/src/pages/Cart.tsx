import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Trash2, ShoppingCart, Plus, Minus } from 'lucide-react';

interface CartItem {
  id: string;
  dataset: {
    id: number;
    name: string;
    slug: string;
    enrichment_level: string;
    total_companies: number;
  };
  quantity: number;
  price_per_company_usd: number;
  subtotal_usd: number;
  subtotal_naira: number;
}

interface CartData {
  items: CartItem[];
  total_usd: number;
  total_naira: number;
  exchange_rate: number;
}

export default function Cart() {
  const [cart, setCart] = useState<CartData | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchCart = async () => {
    try {
      const res = await api.get('/cart');
      setCart(res.data);
    } catch (error) {
      console.error('Failed to fetch cart:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const updateQuantity = async (itemId: string, newQuantity: number) => {
    try {
      await api.put(`/cart/${itemId}`, { quantity: newQuantity });
      fetchCart();
    } catch (error) {
      console.error('Failed to update quantity:', error);
    }
  };

  const removeItem = async (itemId: string) => {
    try {
      await api.delete(`/cart/${itemId}`);
      fetchCart();
    } catch (error) {
      console.error('Failed to remove item:', error);
    }
  };

  const checkout = async () => {
    try {
      const res = await api.post('/purchases', { from_cart: true });
      // Redirect to Paystack
      if (res.data.payment_url) {
        window.location.href = res.data.payment_url;
      }
    } catch (error) {
      console.error('Checkout failed:', error);
      alert('Checkout failed. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-40 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <ShoppingCart className="mx-auto h-24 w-24 text-gray-300 mb-4" />
        <h2 className="text-2xl font-bold text-gray-700 mb-2">Your cart is empty</h2>
        <p className="text-gray-500 mb-8">Add some datasets to get started!</p>
        <button
          onClick={() => navigate('/datasets')}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700"
        >
          Browse Datasets
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Shopping Cart</h1>

      <div className="space-y-4 mb-8">
        {cart.items.map((item) => (
          <div
            key={item.id}
            className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition"
          >
            <div className="flex flex-col md:flex-row justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {item.dataset.name}
                </h3>
                <p className="text-sm text-gray-600 mb-2">
                  {item.dataset.enrichment_level === 'phone_only' ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded bg-blue-100 text-blue-800 text-xs font-medium">
                      Phone Only - $0.05/company
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded bg-green-100 text-green-800 text-xs font-medium">
                      Email & Phone - $0.10/company
                    </span>
                  )}
                </p>
                <p className="text-xs text-gray-500">
                  Max available: {item.dataset.total_companies} companies
                </p>
              </div>

              <div className="flex flex-col items-end gap-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => updateQuantity(item.id, Math.max(1, item.quantity - 10))}
                    className="p-1 rounded border hover:bg-gray-100"
                  >
                    <Minus className="h-4 w-4" />
                  </button>
                  <input
                    type="number"
                    value={item.quantity}
                    onChange={(e) => {
                      const val = parseInt(e.target.value) || 1;
                      if (val > 0 && val <= item.dataset.total_companies) {
                        updateQuantity(item.id, val);
                      }
                    }}
                    className="w-20 text-center border rounded px-2 py-1"
                  />
                  <button
                    onClick={() =>
                      updateQuantity(
                        item.id,
                        Math.min(item.dataset.total_companies, item.quantity + 10)
                      )
                    }
                    className="p-1 rounded border hover:bg-gray-100"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>

                <div className="text-right">
                  <div className="text-lg font-bold text-gray-900">
                    ${item.subtotal_usd.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600">
                    ₦{item.subtotal_naira.toLocaleString('en-NG', { minimumFractionDigits: 2 })}
                  </div>
                </div>

                <button
                  onClick={() => removeItem(item.id)}
                  className="text-red-600 hover:text-red-800 flex items-center gap-1 text-sm"
                >
                  <Trash2 className="h-4 w-4" />
                  Remove
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-gray-50 border rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <span className="text-lg font-semibold">Total</span>
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              ${cart.total_usd.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600">
              ₦{cart.total_naira.toLocaleString('en-NG', { minimumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        <div className="text-xs text-gray-500 mb-4">
          Exchange rate: $1 = ₦{cart.exchange_rate.toFixed(2)}
        </div>

        <button
          onClick={checkout}
          className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold"
        >
          Proceed to Checkout
        </button>
      </div>
    </div>
  );
}
