import { create } from 'zustand'
import { Dataset } from '@/types'

interface DatasetState {
  datasets: Dataset[]
  setDatasets: (datasets: Dataset[]) => void
  addDataset: (dataset: Dataset) => void
}

export const useDatasetStore = create<DatasetState>((set) => ({
  datasets: [],
  setDatasets: (datasets) => set({ datasets }),
  addDataset: (dataset) => set((state) => ({ 
    datasets: [...state.datasets, dataset] 
  })),
}))