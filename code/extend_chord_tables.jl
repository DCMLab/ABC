include("regex.jl")
include("movement_iterator.jl")

using DataFrames

function get_feature(chord, feature, default="", regex=regex)
    m = match(regex, chord)
    m != nothing && m[feature] != nothing ? m[feature] : default
end

function extend_chord_table(df)
    # add column for chord length in beats
    bigrams(iter) = let n = length(iter)
        collect(zip(Iterators.take(iter, n-1), Iterators.drop(iter, 1)))
    end
    df[:length] = [
        map(bg->bg[2]-bg[1], bigrams(df[:totbeat]));
        (eval(parse(replace(df[end, :timesig], "/", "//"))) * 4) + 1 - df[end, :beat]
        ]

    # add global_key column
    df[:global_key] = match(regex, df[1, :chord])[:key]

    # add local_key column
    df[:local_key] = ""
    df[1, :local_key] = "I"

    for i in 2:size(df, 1)
        df[i, :local_key] = get_feature(df[i, :chord], :key, df[i-1, :local_key])
    end

    # add organ column
    df[:pedal] = ""
    df[1, :pedal] = get_feature(df[1, :chord], :pedal)

    for i in 2:size(df, 1)
        m = match(regex, df[i, :chord])
        df[i, :pedal] = if m != nothing && m[:pedal] != nothing
            m[:pedal]
        elseif match(regex, df[i-1, :chord]) != nothing && match(regex, df[i-1, :chord])[:pedalend] != nothing
            ""
        else
            df[i-1, :pedal]
        end
    end

    # add columns for numeral, form, figbass, changes, relativeroot
    for f in (:numeral, :form, :figbass, :changes, :relativeroot)
        df[f] = map(c->get_feature(c, f), df[:chord])
    end

    # add column for phraseend
    df[:phraseend] = map(df[:chord]) do chord
        m = match(regex, chord)
        m != nothing && m[:phraseend] != nothing
    end

    # change NA to "" in altchord column
    df[:altchord] = map(ac -> ismissing(ac) ? "" : ac, df[:altchord])

    df
end

for file in movements()
    # println(file)
    writetable(file, extend_chord_table(readtable(file, nastrings=["NA"])))
end

# create big dataframe
writetable(
    joinpath(@__DIR__, "..", "data", "all_annotations.tsv"),
    vcat(readtable.(movements(), )...),
    nastring="\"\"")
