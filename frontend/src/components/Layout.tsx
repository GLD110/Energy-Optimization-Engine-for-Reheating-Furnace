import { NavLink, Outlet } from "react-router-dom";

const links = [
  ["/", "Furnace live"],
  ["/curve", "Heating curve"],
  ["/energy", "Energy analytics"],
  ["/esg", "CO₂ & ESG"],
  ["/recs", "Recommendations"],
  ["/whatif", "What-if"],
] as const;

export function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">Energy optimization</div>
        <nav className="nav">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
