script_folder="/home/alexander/421702/PPOIS/my-ostis-module/build/Release/generators"
echo "echo Restoring environment" > "$script_folder/deactivate_conanrunenv-release-x86_64.sh"
for v in PATH LD_LIBRARY_PATH DYLD_LIBRARY_PATH
do
    is_defined="true"
    value=$(printenv $v) || is_defined="" || true
    if [ -n "$value" ] || [ -n "$is_defined" ]
    then
        echo export "$v='$value'" >> "$script_folder/deactivate_conanrunenv-release-x86_64.sh"
    else
        echo unset $v >> "$script_folder/deactivate_conanrunenv-release-x86_64.sh"
    fi
done


export PATH="/home/alexander/.conan2/p/b/sc-ma0fc02a1c6c18e/p/bin:$PATH"
export LD_LIBRARY_PATH="/home/alexander/.conan2/p/b/sc-ma0fc02a1c6c18e/p/lib:$LD_LIBRARY_PATH"
export DYLD_LIBRARY_PATH="/home/alexander/.conan2/p/b/sc-ma0fc02a1c6c18e/p/lib:$DYLD_LIBRARY_PATH"