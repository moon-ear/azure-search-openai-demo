"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { getStatus, uploadDocument } from "../../api";
import { Modal, ModalInterface, ModalOptions } from "flowbite";

type SelectedFile = {
    file: File;
    error: boolean;
};

const Upload = () => {
    const $modalElement: HTMLElement | null = document.querySelector("#defaultModal");

    const modalOptions: ModalOptions = {
        placement: "center",
        backdrop: "dynamic",
        backdropClasses: "bg-gray-900 bg-opacity-50 fixed inset-0 z-40",
        closable: true,
        onHide: () => {
            console.log("modal is hidden");
            setSelectedFiles([]); // Clear the selection
            setFileStatuses({});
            const element = document.querySelector(".bg-gray-900.bg-opacity-50.fixed.inset-0.z-40");
            if (element) {
                element.remove();
            }
        },
        onShow: () => {
            console.log("modal is shown");
        },
        onToggle: () => {
            console.log("modal has been toggled");
        }
    };

    const modal: ModalInterface = new Modal($modalElement, modalOptions);

    const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
    const [fileStatuses, setFileStatuses] = useState<{ [fileName: string]: string }>({});
    const [isUploadDone, setIsUploadDone] = useState(false);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files).map(file => {
                return { file, error: !isSupportedFile(file.type) };
            });
            setSelectedFiles(prevFiles => [...prevFiles, ...newFiles]);
        }
    };

    const handleDrop = (e: React.DragEvent<HTMLLabelElement>) => {
        e.preventDefault();
        if (e.dataTransfer.items) {
            const newFiles = Array.from(e.dataTransfer.items)
                .filter(item => item.kind === "file")
                .map(item => {
                    const file = item.getAsFile() as File;
                    return { file, error: !isSupportedFile(file.type) };
                });
            setSelectedFiles(prevFiles => [...prevFiles, ...newFiles]);
        }
    };

    const resetSelectedFiles = () => {
        setSelectedFiles([]);
    };

    const handleDragOver = (e: React.DragEvent<HTMLLabelElement>) => {
        e.preventDefault();
    };

    const handleFileUpload = async () => {
        setIsUploadDone(false);
        if (!selectedFiles || selectedFiles.length === 0) {
            alert("No files selected");
            return;
        }

        console.log("selected files:");
        console.log(selectedFiles);
        modal.show();

        // Initialize statuses as 'pending'
        const initialStatuses: { [fileName: string]: string } = {};
        selectedFiles.forEach(file => (initialStatuses[file.file.name] = "Pending"));
        setFileStatuses(initialStatuses);

        try {
            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                if (isSupportedFile(file.file.type)) {
                    // Start interval to periodically check the status of the file
                    const intervalId = setInterval(async () => {
                        try {
                            const status = await getStatus(file.file.name);
                            setFileStatuses(prevStatuses => ({
                                ...prevStatuses,
                                [file.file.name]: status
                            }));
                        } catch (error) {
                            console.error(`Error fetching status for ${file.file.name}:`, error);
                        }
                    }, 1000); // Check every 1000ms (1 second)

                    await uploadDocument(file.file);

                    // Set the status to 'Uploaded' for the file
                    setFileStatuses(prevStatuses => ({
                        ...prevStatuses,
                        [file.file.name]: "Uploaded"
                    }));

                    // Clear interval when the upload is done
                    clearInterval(intervalId);
                }
            }
        } catch (err) {
            console.error(err);
            alert("There was an error uploading the files");
        }
        setIsUploadDone(true);
    };

    const hideModal = () => {
        modal.hide();
    };

    const statusColorMap = (status: string) => {
        console.log(status);
        if (status) {
            if (status.includes("Uploaded")) {
                return "bg-green-100 text-green-800";
            }
            if (status.includes("Uploading")) {
                return "bg-blue-100 text-blue-800";
            }
            if (status.includes("Processing") || status.includes("Transcribing") || status.includes("Generating")) {
                return "bg-yellow-100 text-yellow-800";
            }
            if (status.includes("Failed")) {
                return "bg-red-100 text-red-800";
            }
            return "bg-gray-100 text-gray-800";
        }
        return "";
    };

    function formatFileSize(bytes: number) {
        if (bytes < 1024) return `${bytes} Bytes`;
        else if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
        else return `${Math.round(bytes / 1024 / 1024)} MB`;
    }

    const isSupportedFile = (fileType: string) => {
        const supportedTypes = ["application/pdf", "audio/mpeg", "audio/wav"];
        return supportedTypes.includes(fileType);
    };

    const supportedFilesCount = selectedFiles.filter(file => isSupportedFile(file.file.type)).length;

    return (
        <>
            <div className="w-1/2 mx-auto pt-8">
                <h1 className="text-center text-3xl mb-3 font-semibold">Upload Multiple Files</h1>

                <div className="flex pt-5 items-center justify-center w-full">
                    <label
                        htmlFor="dropzone-file"
                        onDrop={handleDrop}
                        onDragOver={handleDragOver}
                        className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 dark:hover:bg-bray-800 dark:bg-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-600"
                    >
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                            <svg
                                className="w-8 h-8 mb-4 text-gray-500 dark:text-gray-400"
                                aria-hidden="true"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 20 16"
                            >
                                <path
                                    stroke="currentColor"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"
                                />
                            </svg>
                            <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
                                <span className="font-semibold">Click to upload</span> or drag and drop
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">PDF, MP3, or WAV</p>
                        </div>
                        <input
                            onChange={handleFileChange}
                            id="dropzone-file"
                            type="file"
                            accept="application/pdf,audio/mpeg,audio/wav"
                            className="hidden"
                            multiple
                        />
                    </label>
                </div>

                {/* Uploaded Cards */}
                <div className="mt-4 w-full">
                    {/* Clear All Button */}
                    {selectedFiles.length > 0 ? (
                        <div className="text-right">
                            <button
                                onClick={resetSelectedFiles}
                                type="button"
                                className="inline-flex items-center px-2 py-1 mr-2 text-xs font-medium text-red-800 bg-red-100 rounded hover:bg-red-200 hover:text-red-900"
                            >
                                Clear All
                                <div className="inline-flex items-center p-1 ml-1 text-sm text-red-400 bg-transparent rounded-sm">
                                    <svg className="w-2 h-2" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                                        <path
                                            stroke="currentColor"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"
                                        />
                                    </svg>
                                </div>
                            </button>
                        </div>
                    ) : null}

                    <div className="text-sm mb-1 mr-1 text-right font-semibold text-gray-700"></div>
                    {selectedFiles.map((file, index) => (
                        <div
                            key={index}
                            className={`flex items-center justify-between p-2 mb-2 border ${file.error ? "border-red-500" : "border-gray-300"} rounded-lg`}
                        >
                            <div className="flex items-center">
                                <div className="mr-2 rounded">
                                    <svg
                                        className="w-6 h-5 text-gray-500"
                                        aria-hidden="true"
                                        xmlns="http://www.w3.org/2000/svg"
                                        fill="none"
                                        viewBox="0 0 16 20"
                                    >
                                        <path
                                            stroke="currentColor"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            d="M6 1v4a1 1 0 0 1-1 1H1m14-4v16a.97.97 0 0 1-.933 1H1.933A.97.97 0 0 1 1 18V5.828a2 2 0 0 1 .586-1.414l2.828-2.828A2 2 0 0 1 5.828 1h8.239A.97.97 0 0 1 15 2Z"
                                        />
                                    </svg>
                                </div>
                                {/* Icon placeholder */}
                                <span className="text-sm text-gray-500 break-words">{file.file.name}</span>
                                <h2 className="ml-2 font-semibold text-xs text-gray-500/80 dark:text-gray-400">{formatFileSize(file.file.size)}</h2>
                                {file.error && (
                                    <span className="ml-2 bg-red-100 text-red-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded dark:bg-red-900 dark:text-red-300">
                                        Unsupported File Type
                                    </span>
                                )}
                            </div>
                            <button
                                className="p-2 text-red-600 rounded-full"
                                onClick={() => {
                                    const newFiles = [...selectedFiles];
                                    newFiles.splice(index, 1);
                                    setSelectedFiles(newFiles);
                                }}
                            >
                                <svg className="w-6 h-3 text-gray-800" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                                    <path
                                        stroke="currentColor"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                        d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"
                                    />
                                </svg>
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Upload Button */}
            <div className="pt-5 text-center">
                <button
                    onClick={handleFileUpload}
                    data-modal-target="defaultModal"
                    data-modal-toggle="defaultModal"
                    type="button"
                    disabled={supportedFilesCount < 1}
                    className={`text-white font-medium rounded-lg text-sm px-5 py-2.5 mr-2 mb-2 ${
                        supportedFilesCount < 1
                            ? "bg-gray-400 cursor-not-allowed hover:bg-gray-400 focus:ring-0"
                            : "bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300"
                    }`}
                >
                    Upload
                </button>
            </div>

            {/* Upload Modal */}
            <div
                id="defaultModal"
                // tabIndex="-1"
                data-modal-backdrop="static"
                aria-hidden="true"
                className="fixed top-0 left-0 right-0 z-50 hidden w-full p-4 overflow-x-hidden overflow-y-auto md:inset-0 h-[calc(100%-1rem)] max-h-full"
            >
                <div className="relative w-full max-w-2xl max-h-full">
                    <div className="relative bg-white rounded-lg shadow">
                        <div className="flex items-start justify-between p-4 border-b rounded-t">
                            <h3 className="text-xl font-semibold text-gray-900">Upload Files</h3>
                            <button
                                type="button"
                                className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ml-auto inline-flex justify-center items-center"
                                data-modal-hide="defaultModal"
                            >
                                <svg className="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                                    <path
                                        stroke="currentColor"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth="2"
                                        d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"
                                    />
                                </svg>
                                <span className="sr-only">Close modal</span>
                            </button>
                        </div>
                        <div className="p-6 space-y-6">
                            <div className="relative overflow-x-auto">
                                <table className="w-full text-sm text-left text-gray-500 dark:text-gray-400">
                                    <thead className="text-xs text-gray-700 uppercase dark:bg-gray-700 dark:text-gray-400">
                                        <tr>
                                            <th scope="col" className="px-6 py-3">
                                                File name
                                            </th>
                                            <th scope="col" className="px-6 py-3">
                                                Status
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {selectedFiles
                                            .filter(file => isSupportedFile(file.file.type))
                                            .map((file, index) => (
                                                <tr key={index} className="bg-white border-b dark:bg-gray-800">
                                                    <th scope="row" className="px-6 py-4 font-medium text-gray-900 whitespace-normal ">
                                                        {file.file.name}
                                                    </th>
                                                    <td className="px-6 py-4">
                                                        <span
                                                            className={`${
                                                                statusColorMap(fileStatuses[file.file.name]) || "bg-gray-100 text-gray-800"
                                                            } text-xs font-medium mr-2 px-2.5 py-0.5 rounded`}
                                                        >
                                                            {fileStatuses[file.file.name] || "Pending"}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div className="flex items-center p-6 space-x-2 border-t border-gray-200 rounded-b ">
                            <button
                                data-modal-hide="defaultModal"
                                type="button"
                                disabled={!isUploadDone}
                                onClick={hideModal}
                                className={`text-white ${
                                    isUploadDone ? "bg-blue-700 hover:bg-blue-800" : "bg-gray-400 cursor-not-allowed"
                                } focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center`}
                            >
                                Done
                            </button>
                            <button
                                data-modal-hide="defaultModal"
                                type="button"
                                onClick={hideModal}
                                className="text-gray-500 bg-white hover:bg-gray-100 focus:ring-4 focus:outline-none focus:ring-blue-300 rounded-lg border border-gray-200 text-sm font-medium px-5 py-2.5 hover:text-gray-900 focus:z-10 "
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Upload;
