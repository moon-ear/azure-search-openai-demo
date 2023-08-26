import { Outlet } from "react-router-dom";

import styles from "./Layout.module.css";
import { Sidebar } from "../../components/Sidebar";

const Layout = () => {
    return (
        <div className={styles.layout}>
            <Sidebar />

            <Outlet />
        </div>
    );
};

export default Layout;
