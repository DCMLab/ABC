function movements(dir=joinpath(@__DIR__, "..", "data", "tsv"))
    sub_dirs = filter(isdir, joinpath.(dir, readdir(dir)))
    filter(file->!ismatch(r"\.DS_Store", file),
        vcat(
            map(sub_dirs) do sub_dir
                joinpath.(sub_dir, readdir(sub_dir))
            end...
        )
    )
end
