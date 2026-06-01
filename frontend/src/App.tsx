import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/components/Layout";
import ESG from "@/pages/ESG";
import Energy from "@/pages/Energy";
import HeatingCurve from "@/pages/HeatingCurve";
import Live from "@/pages/Live";
import Recommendations from "@/pages/Recommendations";
import WhatIf from "@/pages/WhatIf";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Live />} />
        <Route path="/curve" element={<HeatingCurve />} />
        <Route path="/energy" element={<Energy />} />
        <Route path="/esg" element={<ESG />} />
        <Route path="/recs" element={<Recommendations />} />
        <Route path="/whatif" element={<WhatIf />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
