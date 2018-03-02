#include <iostream>
#include <apu_version.h>

int main(int argc, char* argv[]) {
    std::cout << "apu_version_string: " << apu_version_string() << std::endl;
}
