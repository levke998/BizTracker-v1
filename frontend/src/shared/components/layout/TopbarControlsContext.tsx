import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type TopbarControlsContextValue = {
  controls: ReactNode;
  setControls: (controls: ReactNode) => void;
};

const TopbarControlsContext = createContext<TopbarControlsContextValue | null>(null);

export function TopbarControlsProvider({ children }: { children: ReactNode }) {
  const [controls, setControls] = useState<ReactNode>(null);
  const value = useMemo(() => ({ controls, setControls }), [controls]);

  return (
    <TopbarControlsContext.Provider value={value}>
      {children}
    </TopbarControlsContext.Provider>
  );
}

export function useTopbarControls() {
  const context = useContext(TopbarControlsContext);
  if (!context) {
    throw new Error("useTopbarControls must be used inside TopbarControlsProvider.");
  }
  return context;
}
