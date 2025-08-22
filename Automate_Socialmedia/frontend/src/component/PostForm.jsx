import React from "react";

function PostForm(){
    return(
        <>
            <div>
                <h2 className="text-red-500">Post on Instagram + Linkedin</h2>
                <form action="" className="bg-indigo-500 flex flex-col gap-6 text-white rounded-2xl p-4 m-auto w-[40%]">
                    <input 
                        className="border-1 outline-0 border-amber-50 rounded-2xl px-2 py-3 w-[80%]"
                        type="text" 
                        placeholder="Enter the caption"
                        name="caption" 
                        id="caption"  
                    />
                    <input 
                        className="file:border-1 file:border-amber-50 file:rounded-2xl file:p-2 file:w-[40%] file:m-1"
                        type="file" 
                        name="fileName" 
                        id="file" 
                    />
                    <button className="bg-amber-700 text-white rounded-2xl font-bold p-2.5" type="submit">
                        Post
                    </button>
                </form>
            </div>
        </>
    )
}

export default PostForm;