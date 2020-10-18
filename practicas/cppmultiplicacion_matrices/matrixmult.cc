#include <iostream>
#include <vector>



#include "Matrix.hh"
using namespace std;




int main()
{   

    for (size_t i = 10; i < 500; i+=10)
    {
        auto startf = std::chrono::system_clock::now();
        Matrix <int> a(i,i);
        a.fill();
        Matrix <int> b(i,i);
        b = a;
        // b.fill();
        auto endf = std::chrono::system_clock::now();
        std::chrono::duration<double> elapsed_secondsf = endf-startf;
        std::cout<<"Filling time: "<< elapsed_secondsf.count() << endl;

        auto start = std::chrono::system_clock::now();
        a.mult(b);
        auto end = std::chrono::system_clock::now();
        std::chrono::duration<double> elapsed_seconds = end-start;
        
        start = std::chrono::system_clock::now();
        a.mult2(b);
        end = std::chrono::system_clock::now();
        std::chrono::duration<double> elapsed_seconds2 = end-start;
        std::cout<<"n: "<< i<< endl;
        std::cout<<"Mult 1: "<< elapsed_seconds.count();
        std::cout<<"Mult 2: "<< elapsed_seconds2.count()<<endl;
    }
    return 0;
}