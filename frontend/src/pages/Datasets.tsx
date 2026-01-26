
import { useEffect, useState } from 'react';
import api from '../lib/axios'; // Import the axios instance

interface Dataset {
  id: string;
  name: string;
  slug: string;
  description: string;
  price: number;
  company_count: number;
  // ... other fields
}

const Datasets = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // This will call /api/v1/datasets through Nginx
      const response = await api.get('/v1/datasets');
      
      setDatasets(response.data);
    } catch (err: any) {
      console.error('Error fetching datasets:', err);
      setError(err.message || 'Failed to load datasets');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Datasets</h1>
      {datasets.map((dataset) => (
        <div key={dataset.id}>
          <h3>{dataset.name}</h3>
          <p>{dataset.description}</p>
          <p>Price: ${dataset.price}</p>
        </div>
      ))}
    </div>
  );
};

export default Datasets;