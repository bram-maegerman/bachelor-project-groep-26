export default function Header() {
    return (
    <div className="relative flex items-center p-3" style={{ backgroundColor: "#00407A", height: "100px"}}>
        <div className="flex items-center justify-start w-1/3">
        <button
            className="rounded-2xl text-white p-1 cursor-pointer bg-[#52bdec] hover:bg-blue-500"
        >
            <p className="ml-1">Instellingen ⚙️</p>
        </button>
        </div>

        <div className="absolute left-1/2 transform -translate-x-1/2">
            <img
                src="/KULEUVEN_BIB_LOGO.png"
                height="50"
                width="300"
                alt="KUL bibliotheken logo"
            />
        </div>
    </div>
    );

}