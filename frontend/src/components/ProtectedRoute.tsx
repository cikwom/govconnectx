import {Navigate,Outlet,useLocation} from "react-router-dom";import {useAuth} from "../state/AuthContext";
export default function ProtectedRoute(){const{user,loading}=useAuth();const location=useLocation();if(loading)return <div className="screen-state">Checking your session…</div>;if(!user)return <Navigate to="/login" replace state={{from:location}}/>;return <Outlet/>}
