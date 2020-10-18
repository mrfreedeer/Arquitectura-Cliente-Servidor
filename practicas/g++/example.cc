#include<iostream>
#include<zmqpp/zmqpp.hpp>
#include<thread>

using namespace std;
using namespace zmqpp;

int main() {
    context ctx;
    socket work(ctx, socket_type::pull);

    cout << "hello"<< endl;
    return 0;
}
