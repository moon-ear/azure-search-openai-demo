import { useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";

export const Sidebar = () => {
    const location = useLocation(); // Get the current location object from react-router

    useEffect(() => {
        console.log(window.location);

        // If you want to update window.location, you can do so here.
        // However, be cautious as this can cause the page to refresh.
        // window.location.href = someNewURL;
    }, [location]); // The effect depends on the location, so it'll re-run whenever location changes
    return (
        <div className="w-64 px-3 py-4 overflow-y-auto bg-gray-50">
            <ul className="space-y-2 font-medium">
                <li>
                    <NavLink
                        to="/"
                        className={`flex items-center p-2 text-gray-900 rounded-lg ${
                            window.location.hash === "/" || window.location.hash === "#/" ? "bg-blue-500 text-white" : "hover:bg-gray-200"
                        }`}
                    >
                        <svg
                            width="21"
                            height="20"
                            className={`h-6 text-gray-500 transition duration-75 group-hover:text-gray-900 ${
                                window.location.hash === "/" || window.location.hash === "#/" ? "text-white" : null
                            }`}
                            viewBox="0 0 21 20"
                            fill="currentColor"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path d="M0 3.15789C0 2.32037 0.331874 1.51715 0.922614 0.924926C1.51335 0.332705 2.31457 0 3.15 0H17.85C18.6854 0 19.4866 0.332705 20.0774 0.924926C20.6681 1.51715 21 2.32037 21 3.15789V13.6842C21 14.5217 20.6681 15.3249 20.0774 15.9171C19.4866 16.5094 18.6854 16.8421 17.85 16.8421H5.95035C5.72316 16.8421 5.5021 16.916 5.32035 17.0526L1.68 19.7895C1.524 19.9067 1.33851 19.9782 1.1443 19.9958C0.950082 20.0132 0.754834 19.9763 0.580429 19.8888C0.406014 19.8015 0.259329 19.667 0.156817 19.5007C0.0542954 19.3345 0 19.1428 0 18.9474V3.15789ZM5.25 3.15789C4.97152 3.15789 4.70445 3.2688 4.50753 3.4662C4.31063 3.66361 4.2 3.93134 4.2 4.21052C4.2 4.4897 4.31063 4.75744 4.50753 4.95485C4.70445 5.15225 4.97152 5.26315 5.25 5.26315H15.75C16.0285 5.26315 16.2956 5.15225 16.4925 4.95485C16.6893 4.75744 16.8 4.4897 16.8 4.21052C16.8 3.93134 16.6893 3.66361 16.4925 3.4662C16.2956 3.2688 16.0285 3.15789 15.75 3.15789H5.25ZM5.25 7.36842C4.97152 7.36842 4.70445 7.47936 4.50753 7.67673C4.31063 7.8741 4.2 8.14189 4.2 8.42105C4.2 8.7002 4.31063 8.96799 4.50753 9.16536C4.70445 9.36273 4.97152 9.47368 5.25 9.47368H15.75C16.0285 9.47368 16.2956 9.36273 16.4925 9.16536C16.6893 8.96799 16.8 8.7002 16.8 8.42105C16.8 8.14189 16.6893 7.8741 16.4925 7.67673C16.2956 7.47936 16.0285 7.36842 15.75 7.36842H5.25ZM5.25 11.5789C4.97152 11.5789 4.70445 11.6899 4.50753 11.8873C4.31063 12.0846 4.2 12.3524 4.2 12.6316C4.2 12.9107 4.31063 13.1785 4.50753 13.3759C4.70445 13.5733 4.97152 13.6842 5.25 13.6842H9.45C9.72846 13.6842 9.99558 13.5733 10.1925 13.3759C10.3893 13.1785 10.5 12.9107 10.5 12.6316C10.5 12.3524 10.3893 12.0846 10.1925 11.8873C9.99558 11.6899 9.72846 11.5789 9.45 11.5789H5.25Z" />
                        </svg>
                        <span className="flex-1 ml-3 whitespace-nowrap">Chat</span>
                    </NavLink>
                </li>
                <li>
                    <NavLink
                        to="/knowledge-base"
                        className={`flex items-center p-2 text-gray-900 rounded-lg ${
                            window.location.href.includes("/knowledge-base") ? "bg-blue-500 text-white" : "hover:bg-gray-200"
                        }`}
                    >
                        <svg
                            width="24"
                            className={`h-6 text-gray-500 transition duration-75 group-hover:text-gray-900 ${
                                window.location.href.includes("/knowledge-base") ? "text-white" : null
                            }`}
                            height="20"
                            viewBox="0 0 27 20"
                            fill="currentColor"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path d="M4.00454 0C4.00384 0 4.00304 0 4.00234 0C3.75474 0 3.52187 0.0965165 3.34602 0.271921C3.16824 0.449265 3.07031 0.6854 3.07031 0.936784V14.9837C3.07031 15.4988 3.49102 15.9189 4.00824 15.9202C6.18872 15.9254 9.8419 16.3799 12.3621 19.0172V4.31672C12.3621 4.14211 12.3175 3.97807 12.2333 3.84233C10.1649 0.511229 6.18996 0.00511229 4.00454 0Z" />
                            <path d="M23.1082 14.9838V0.936784C23.1082 0.6854 23.0103 0.449265 22.8325 0.271921C22.6567 0.0965165 22.4236 0 22.1763 0C22.1755 0 22.1747 0 22.174 0C19.9887 0.00520044 16.0138 0.511317 13.9452 3.84242C13.861 3.97816 13.8165 4.14219 13.8165 4.3168V19.0172C16.3367 16.3799 19.9899 15.9254 22.1704 15.9202C22.6875 15.9189 23.1082 15.4988 23.1082 14.9838Z" />
                            <path d="M25.2417 3.23975H24.5625V14.984C24.5625 16.2992 23.4909 17.3716 22.1737 17.3749C20.3242 17.3793 17.2746 17.7409 15.1149 19.7851C18.8502 18.8705 22.7879 19.465 25.032 19.9764C25.3122 20.0402 25.6018 19.9743 25.8263 19.7954C26.05 19.6169 26.1783 19.3501 26.1783 19.0637V4.17635C26.1784 3.65992 25.7581 3.23975 25.2417 3.23975Z" />
                            <path d="M1.61584 14.984V3.23975H0.936608C0.420266 3.23975 0 3.65992 0 4.17635V19.0634C0 19.3499 0.128336 19.6166 0.352043 19.7951C0.576367 19.974 0.865653 20.0402 1.1463 19.9762C3.39042 19.4647 7.32821 18.8702 11.0634 19.7848C8.90368 17.7408 5.85411 17.3792 4.0046 17.3748C2.68748 17.3716 1.61584 16.2992 1.61584 14.984Z" />
                        </svg>

                        <span className="flex-1 ml-3 whitespace-nowrap">Knowledge Base</span>
                    </NavLink>
                </li>
                <li>
                    <NavLink
                        to="/upload"
                        className={`flex items-center p-2 text-gray-900 rounded-lg ${
                            window.location.href.includes("/upload") ? "bg-blue-500 text-white" : "hover:bg-gray-200"
                        }`}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 24 24"
                            className={`w-6 h-6 text-gray-500 transition duration-75 group-hover:text-gray-900 ${
                                window.location.href.includes("/upload") ? "text-white" : null
                            }`}
                            fill="currentColor"
                        >
                            <path d="M11.47 1.72a.75.75 0 011.06 0l3 3a.75.75 0 01-1.06 1.06l-1.72-1.72V7.5h-1.5V4.06L9.53 5.78a.75.75 0 01-1.06-1.06l3-3zM11.25 7.5V15a.75.75 0 001.5 0V7.5h3.75a3 3 0 013 3v9a3 3 0 01-3 3h-9a3 3 0 01-3-3v-9a3 3 0 013-3h3.75z" />
                        </svg>

                        <span className="flex-1 ml-3 whitespace-nowrap">Upload</span>
                    </NavLink>
                </li>
            </ul>
        </div>
    );
};
