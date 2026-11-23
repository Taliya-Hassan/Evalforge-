import { Link, Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { getToken, setToken } from "./api";
import DiffView from "./pages/DiffView";
import Login from "./pages/Login";
import ProjectDetail from "./pages/ProjectDetail";
import Projects from "./pages/Projects";
import RunView from "./pages/RunView";
import SuiteDetail from "./pages/SuiteDetail";

function Layout() {
  const nav = useNavigate();
  if (!getToken()) return <Navigate to="/login" replace />;
  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">EvalForge</Link>
        <button
          className="link"
          onClick={() => {
            setToken(null);
            nav("/login");
          }}
        >
          Log out
        </button>
      </header>
      <main className="container">
        <Outlet />
      </main>
    </>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/" element={<Projects />} />
        <Route path="/projects/:projectId" element={<ProjectDetail />} />
        <Route path="/suites/:suiteId" element={<SuiteDetail />} />
        <Route path="/suites/:suiteId/diff" element={<DiffView />} />
        <Route path="/runs/:runId" element={<RunView />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
